### 1 — High‑Level Description

Build **WhisperFlow‑Py**, a menu‑bar‑only macOS utility that transcribes speech while you either **hold** a modifier key (Ctrl) or **toggle** a shortcut (⇧⌘/). When recording stops it:

1. Sends audio to **OpenAI Whisper** for transcription.  
2. Passes the transcript to **GPT‑4o‑mini** to add punctuation / formatting.  
3. Copies the cleaned text to the clipboard and triggers ⌘ V to paste it into the active field.  
4. Shows status via a menu‑bar glyph (🜏 idle → ◉ rec → … format → ✓ done).  

Packages: `rumps`, `pyobjc`, `sounddevice`, `numpy`, `quickmachotkey`, `openai`, `py2app`.

---

### 2 — Directory Structure

```
whisperflow/
│
├─ pyproject.toml          # Poetry config (+ build backend)
├─ README.md
│
├─ main.py                 # app entry + state machine
├─ hotkeys.py              # Quartz event tap for hold / toggle keys
├─ audio.py                # Recorder class with silence detection
├─ stt.py                  # Whisper REST helper
├─ llm.py                  # GPT‑4o formatter
├─ ui.py                   # menu‑bar icon helpers + paste logic
│
├─ packaging/
│   ├─ setup.py            # py2app build script
│   └─ com.whisperflow.plist   # LaunchAgent template
└─ tests/
    └─ test_roundtrip.py
```

---

### 3 — Step‑by‑Step Development Process

#### 3.1 — Create and activate environment

```bash
brew install python
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install rumps pyobjc sounddevice numpy quickmachotkey openai py2app
```

Add your key:

```bash
echo 'export OPENAI_API_KEY="sk‑live‑…"' >> ~/.zshrc && source ~/.zshrc
```

#### 3.2 — Write modules

**hotkeys.py**

```python
import Quartz, asyncio

HOLD_VK   = Quartz.kVK_Control
TOGGLE_VK = Quartz.kVK_ANSI_Slash
TOGGLE_FL = Quartz.kCGEventFlagMaskShift | Quartz.kCGEventFlagMaskCommand
_queue    = asyncio.Queue()

def events(): return _queue

def _tap(proxy, type_, event, refcon):
    vk = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
    fl = Quartz.CGEventGetFlags(event)
    dn = type_ == Quartz.kCGEventKeyDown
    if vk == HOLD_VK and fl & Quartz.kCGEventFlagMaskControl:
        _queue.put_nowait(("hold", "down" if dn else "up"))
    elif vk == TOGGLE_VK and dn and (fl & TOGGLE_FL) == TOGGLE_FL:
        _queue.put_nowait(("toggle", "press"))
    return event

def start():
    tap = Quartz.CGEventTapCreate(
        Quartz.kCGSessionEventTap, Quartz.kCGHeadInsertEventTap, 0,
        Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)|Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp),
        _tap, None)
    src = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
    Quartz.CFRunLoopAddSource(Quartz.CFRunLoopGetCurrent(), src,
                              Quartz.kCFRunLoopCommonModes)
    Quartz.CGEventTapEnable(tap, True)
```

**audio.py**

```python
import sounddevice as sd, numpy as np, wave, tempfile, asyncio

SR, CH = 16000, 1
SILENCE_DB, HANG = -45, 0.8

class Recorder:
    def __init__(self): self._buf, self._stream = [], None
    async def start(self):
        self._buf, self._stream = [], sd.InputStream(samplerate=SR, channels=CH, dtype="int16")
        self._stream.start()
        asyncio.create_task(self._collect())
    async def _collect(self):
        silent = 0
        while self._stream:
            await asyncio.sleep(0)
            blk,_ = self._stream.read(1024); self._buf.append(blk.copy())
            rms = 20*np.log10(np.sqrt(np.mean(blk.astype(float)**2))+1e-5)
            silent = silent+1024/SR if rms < SILENCE_DB else 0
            if silent > HANG: break
    async def stop(self):
        self._stream.stop(); self._stream.close(); self._stream = None
        wav = np.concatenate(self._buf)
        path = tempfile.mktemp(suffix=".wav")
        with wave.open(path,"wb") as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes(wav.tobytes())
        return path
```

**stt.py**

```python
import openai, asyncio, os, functools
openai.api_key = os.environ["OPENAI_API_KEY"]

async def transcribe(path: str) -> str:
    loop = asyncio.get_event_loop()
    with open(path,"rb") as f:
        fn = functools.partial(openai.audio.transcriptions.create, model="whisper-1", file=f)
        rsp = await loop.run_in_executor(None, fn)
    return rsp.text.strip()
```

**llm.py**

```python
import openai, asyncio, functools, os
openai.api_key = os.environ["OPENAI_API_KEY"]
SYSTEM = "Clean up punctuation and capitalization. Respond with the corrected text only."
async def format_text(raw: str) -> str:
    msgs=[{"role":"system","content":SYSTEM},{"role":"user","content":raw}]
    loop=asyncio.get_event_loop()
    fn=functools.partial(openai.chat.completions.create,
                         model="gpt-4o-mini", messages=msgs, temperature=0.2)
    rsp=await loop.run_in_executor(None,fn)
    return rsp.choices[0].message.content.strip()
```

**ui.py**

```python
import AppKit, Quartz, time

class MenuIcon:
    idle="🜏"
    @staticmethod
    def set(app,g): app.title=g
    @staticmethod
    def listen(a): MenuIcon.set(a,"◉")
    @staticmethod
    def think(a):  MenuIcon.set(a,"…")
    @staticmethod
    def success(a): MenuIcon.set(a,"✓"); AppKit.NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(1,a,"reset:",None,False)
    @staticmethod
    def reset_(self,_): MenuIcon.set(self,MenuIcon.idle)

def paste_text(txt:str):
    pb=AppKit.NSPasteboard.generalPasteboard(); pb.clearContents(); pb.setString_forType_(txt,AppKit.NSStringPboardType)
    src=Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateCombinedSessionState)
    for d in (True,False):
        ev=Quartz.CGEventCreateKeyboardEvent(src,9,d); Quartz.CGEventSetFlags(ev,Quartz.kCGEventFlagMaskCommand)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap,ev); time.sleep(0.01)
```

**main.py**

```python
import asyncio, rumps
from hotkeys import start as hotkeys_start, events as hk_events
from audio  import Recorder
from stt    import transcribe
from llm    import format_text
from ui     import MenuIcon, paste_text

STATE, rec = "IDLE", Recorder()

async def finish(app):
    global STATE
    STATE="BUSY"; MenuIcon.think(app)
    path=await rec.stop(); raw=await transcribe(path); txt=await format_text(raw)
    paste_text(txt); MenuIcon.success(app); STATE="IDLE"

async def handler(app,kind,act):
    global STATE
    if STATE=="BUSY": return
    if kind=="hold":
        if act=="down" and STATE=="IDLE": await rec.start(); MenuIcon.listen(app); STATE="REC_HOLD"
        elif act=="up" and STATE=="REC_HOLD": await finish(app)
    elif kind=="toggle" and act=="press":
        if STATE=="IDLE": await rec.start(); MenuIcon.listen(app); STATE="REC_TOGGLE"
        elif STATE=="REC_TOGGLE": await finish(app)

class WhisperFlow(rumps.App):
    def __init__(self): super().__init__(MenuIcon.idle, quit_button=None); self.menu=["Quit"]; self.menu["Quit"].set_callback(lambda _: rumps.quit_application())
    def run_loop(self):
        hotkeys_start()
        loop=asyncio.get_event_loop()
        loop.create_task(self.worker()); super().run()
    async def worker(self):
        async for k,a in hk_events(): await handler(self,k,a)

if __name__=="__main__":
    WhisperFlow().run_loop()
```

#### 3.3 — Package as a `.app`

`packaging/setup.py`

```python
from setuptools import setup
OPTIONS={"argv_emulation":False,"plist":{"LSUIElement":True,"CFBundleName":"WhisperFlow","NSMicrophoneUsageDescription":"Needed to transcribe speech."}}
setup(app=["main.py"],options={"py2app":OPTIONS},setup_requires=["py2app"])
```

Build:

```bash
python packaging/setup.py py2app
open dist             # drag WhisperFlow.app into /Applications
```

#### 3.4 — Launch at login

`packaging/com.whisperflow.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.whisperflow</string>
  <key>ProgramArguments</key><array><string>/Applications/WhisperFlow.app/Contents/MacOS/WhisperFlow</string></array>
  <key>RunAtLoad</key><true/>
</dict></plist>
```

```bash
cp packaging/com.whisperflow.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.whisperflow.plist
```

#### 3.5 — Test

```bash
pytest tests/            # after mocking OpenAI calls
```

Grant Microphone, Input Monitoring, and Accessibility permissions on first run, then hold Ctrl or tap ⇧⌘/ to dictate and paste.