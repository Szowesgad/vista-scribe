# WhisperFlow-Py

WhisperFlow-Py is a menu-bar-only macOS utility designed for quick and seamless speech-to-text transcription. It listens for specific hotkeys, records audio, transcribes it using OpenAI Whisper, formats the text using GPT-4o-mini, and automatically pastes the result into the active application.

## Features

- **Menu Bar Interface:** Runs discreetly in the macOS menu bar.
- **Hotkey Activation:**
  - **Hold Mode:** Hold the `Control` key to record.
  - **Toggle Mode:** Press `Shift + Command + /` (⇧⌘/) to start/stop recording.
- **OpenAI Integration:**
  - Uses Whisper API for transcription.
  - Uses GPT-4o-mini API for punctuation and capitalization cleanup.
- **Automatic Pasting:** Copies the final text to the clipboard and simulates `Command + V` (⌘V).
- **Status Indicators:** Menu bar icon changes to show status (Idle: 🜏, Recording: ◉, Processing: …, Success: ✓).
- **Silence Detection:** Automatically stops recording after a short period of silence (currently ~0.8 seconds).

## Setup

### Prerequisites

- macOS
- [Homebrew](https://brew.sh/) (for installing Python)
- Python 3.9+
- An OpenAI API Key

### Installation Steps

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/AlexHagemeister/wisprflow-clone.git
    cd wisprflow-clone
    ```

2.  **Install Python (if needed):**

    ```bash
    brew install python
    ```

3.  **Create Virtual Environment:**

    ```bash
    python3 -m venv .venv
    ```

4.  **Activate Environment:**

    ```bash
    source .venv/bin/activate
    ```

    _(Your terminal prompt should now start with `(.venv)`)_

5.  **Install Dependencies:**

    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

6.  **Configure API Key:**
    - Create a file named `.env` in the project root directory.
    - Add your OpenAI API key to it:
      ```env
      OPENAI_API_KEY="sk-YOUR_API_KEY_HERE"
      ```
    - _(Note: The `.env` file is included in `.gitignore` to prevent accidentally committing your key.)_

## Usage (Running from Source)

1.  **Activate Environment:**

    ```bash
    source .venv/bin/activate
    ```

2.  **Run the Application:**

    ```bash
    python main.py
    ```

3.  **Grant Permissions (First Run):**
    macOS will prompt you to grant permissions:

    - **Microphone Access:** Needed for recording audio.
    - **Accessibility Access:** Needed for simulating the paste command (⌘V).
    - **Input Monitoring:** Needed to detect the global hotkeys (Ctrl, ⇧⌘/).
      _You may need to manually enable these for your Terminal application or Python itself in **System Settings > Privacy & Security**._

4.  **Transcribe:**

    - Click into any text field where you want to paste text.
    - **Hold Mode:** Press and hold the `Control` key, speak your phrase clearly, and release the key.
    - **Toggle Mode:** Press `Shift + Command + /`, speak your phrase, and press `Shift + Command + /` again.
    - The menu bar icon will indicate the status (◉ → … → ✓).
    - The transcribed and formatted text should automatically paste into the active field.

5.  **Quit:** Click the menu bar icon (🜏) and select "Quit".

## Packaging (`.app` Bundle)

_(Note: See 'Current Status' below regarding build issues.)_

1.  **Activate Environment:**

    ```bash
    source .venv/bin/activate
    ```

2.  **Navigate to Packaging Directory:**

    ```bash
    cd packaging
    ```

3.  **Run py2app:**

    ```bash
    python setup.py py2app
    ```

4.  **Find the App:** The `WhisperFlow.app` bundle will be created in the `packaging/dist/` directory.

5.  **Install & Run:**
    - Drag `WhisperFlow.app` to your `/Applications` folder.
    - Double-click the app in `/Applications` to run it.
    - Grant Microphone, Accessibility, and Input Monitoring permissions again, this time specifically for `WhisperFlow.app`.

## Launch at Login

_(This requires a working `.app` bundle placed in `/Applications`)_

1.  **Copy LaunchAgent Plist:**

    ```bash
    cp packaging/com.whisperflow.plist ~/Library/LaunchAgents/
    ```

2.  **Load LaunchAgent:**
    ```bash
    launchctl load ~/Library/LaunchAgents/com.whisperflow.plist
    ```

WhisperFlow should now launch automatically the next time you log in. To unload it:

```bash
launchctl unload ~/Library/LaunchAgents/com.whisperflow.plist
rm ~/Library/LaunchAgents/com.whisperflow.plist
```

## Current Status & Known Issues

- **Core Functionality:** The application runs correctly when launched from source code via `python main.py`. Hotkeys, recording, transcription, formatting, and pasting are functional.
- **`.app` Build:** The application bundle created by `py2app` currently **fails to launch**. Debugging indicates an issue with packaging or finding the `libportaudio.dylib` library required by the `sounddevice` package within the bundled environment (`OSError: PortAudio library not found`). Attempts to fix this by explicitly including `sounddevice` in `setup.py` packages have not yet resolved the launch error. Further investigation into `py2app` configuration or potential workarounds (like manually including the dylib) is needed.

## License

MIT License (See LICENSE file for details)
