# main.py
#
# purpose: entry point for the whisperflow application. initializes and runs the
#          macos menu bar app, manages the application's state machine, and
#          coordinates interactions between hotkey detection, audio recording,
#          transcription, formatting, and ui updates.
#
# dependencies: asyncio (core async operations)
#               rumps (macos menu bar app framework)
#               hotkeys.py (provides hotkey events)
#               audio.py (provides recorder class)
#               stt.py (provides transcription function)
#               llm.py (provides text formatting function)
#               ui.py (provides menu icon updates and paste function)
#               logging (for application-level logging)
#
# key components: whisperflow class (subclass of rumps.app)
#                 state machine logic (idle, rec_hold, rec_toggle, busy)
#                 async worker task to process hotkey events
#
# design rationale: uses rumps for simple menu bar integration on macos.
#                   employs an async event loop to handle concurrent tasks like
#                   listening for hotkeys and processing audio/api calls without
#                   blocking the main thread. a simple state machine ensures
#                   predictable behavior based on user input and processing status.
#
import asyncio
import rumps
import logging
import os
import objc  # for selector
import threading  # for asyncio thread
import queue  # for checking standard queue

# import our modules
from hotkeys import start as hotkeys_start, events as hk_events
from audio import Recorder
from stt import transcribe
from llm import format_text
from ui import MenuIcon, paste_text

# --- global state ---

# application state machine
# possible states: idle, rec_hold, rec_toggle, busy
STATE = "IDLE"
# global recorder instance
recorder = Recorder()

# configure logging (set level for the entire application)
# consider moving this to a dedicated config area if app grows
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- core logic functions ---


async def finish_recording(app: rumps.App):
    """handles the process after recording stops.

    stops recorder, transcribes, formats, pastes, updates ui, and resets state.
    includes error handling for transcription and formatting steps.

    args:
        app (rumps.app): the main application instance.
    """
    global STATE
    if STATE == "IDLE" or STATE == "BUSY":  # shouldn't happen, but safeguard
        logger.warning(f"finish_recording called unexpectedly in state: {STATE}")
        return

    logger.info(f"Finishing recording (current state: {STATE})")
    previous_state = STATE
    STATE = "BUSY"
    MenuIcon.think(app)

    try:
        # 1. stop recording and get audio path
        path = await recorder.stop()
        if not path:
            logger.error("Audio recording failed or produced no file.")
            # reset state without success indication
            MenuIcon.set(app, MenuIcon.idle)
            STATE = "IDLE"
            return

        # 2. transcribe audio
        logger.info(f"Transcribing audio file: {path}")
        raw_text = await transcribe(path)
        if raw_text is None:
            logger.error("Transcription failed.")
            # optionally notify user via menu?
            MenuIcon.set(app, MenuIcon.idle)  # reset state
            STATE = "IDLE"
            # clean up the temp file if transcription fails
            if os.path.exists(path):
                try:
                    os.remove(path)  # <-- re-enable deletion
                    logger.info(f"Cleaned up temp file (finally block): {path}")
                except OSError as e:
                    logger.error(
                        f"Failed to remove temp file {path} in finally block: {e}"
                    )
            return
        logger.info(f"Raw transcript: '{raw_text[:50]}...'")

        # 3. format text (optional, proceed even if formatting fails?)
        logger.info("Formatting transcript...")
        formatted_text = await format_text(raw_text)
        if formatted_text is None:
            logger.warning("Text formatting failed. Pasting raw transcript instead.")
            text_to_paste = raw_text  # fallback to raw text
        else:
            text_to_paste = formatted_text
            logger.info(f"Formatted text: '{text_to_paste[:50]}...'")

        # 4. paste text
        if text_to_paste:
            paste_text(text_to_paste)
        else:
            logger.warning("No text available to paste after processing.")

        # 5. indicate success and reset state
        MenuIcon.success(app)  # success() handles timer to reset icon later
        STATE = "IDLE"
        logger.info("Processing finished successfully.")

    except Exception as e:
        logger.error(
            f"An unexpected error occurred during finish_recording: {e}", exc_info=True
        )
        MenuIcon.set(app, MenuIcon.idle)  # reset state on error
        STATE = "IDLE"
    finally:
        # ensure temp file is cleaned up if it still exists (e.g., if formatting failed)
        if "path" in locals() and path and os.path.exists(path):
            try:
                os.remove(path)  # <-- re-enable deletion
                logger.info(f"Cleaned up temp file (finally block): {path}")
            except OSError as e:
                logger.error(f"Failed to remove temp file {path} in finally block: {e}")


async def handle_hotkey_event(app: rumps.App, key_type: str, action: str):
    """handles incoming hotkey events based on the current application state.

    manages state transitions (idle -> rec_hold/rec_toggle -> busy -> idle).

    args:
        app (rumps.app): the main application instance.
        key_type (str): 'hold' or 'toggle'.
        action (str): 'down', 'up', or 'press'.
    """
    global STATE
    logger.info(
        f"--- Handling event: type={key_type}, action={action}, current_state={STATE} ---"
    )
    logger.debug(
        f"Hotkey event received: type={key_type}, action={action}, current_state={STATE}"
    )

    if STATE == "BUSY":
        logger.warning("Hotkey event ignored: application is busy.")
        return

    if key_type == "hold":
        if action == "down" and STATE == "IDLE":
            try:
                logger.info(">>> Attempting to start recording (Hold Down)...")
                await recorder.start()
                # recorder started successfully, now update ui and state
                logger.info(">>> Recorder started, attempting to set icon to listen...")
                MenuIcon.listen(app)
                STATE = "REC_HOLD"
                logger.info("State transition: IDLE -> REC_HOLD")
            except Exception as e:
                # This catches errors from recorder.start() only
                logger.error(
                    f"Failed to start recording on hold-down: {e}", exc_info=True
                )
                # Reset state and attempt cleanup if start failed
                MenuIcon.set(app, MenuIcon.idle)
                STATE = "IDLE"
                # Attempt graceful stop to clean up recorder state if needed
                if recorder._stream:  # Check if stream was partially created
                    logger.warning("Attempting recorder cleanup after start failure...")
                    try:
                        await recorder.stop()
                    except Exception as stop_e:
                        logger.error(f"Error during cleanup recorder.stop: {stop_e}")
        elif action == "up" and STATE == "REC_HOLD":
            logger.info(">>> Attempting to finish recording (Hold Up)...")
            logger.info("Hold key released, initiating finish sequence.")
            await finish_recording(app)
            # state becomes busy then idle within finish_recording

    elif key_type == "toggle" and action == "press":
        if STATE == "IDLE":
            try:
                logger.info(">>> Attempting to start recording (Toggle Press IDLE)...")
                await recorder.start()
                # recorder started successfully, now update ui and state
                logger.info(">>> Recorder started, attempting to set icon to listen...")
                MenuIcon.listen(app)
                STATE = "REC_TOGGLE"
                logger.info("State transition: IDLE -> REC_TOGGLE")
            except Exception as e:
                # This catches errors from recorder.start() only
                logger.error(
                    f"Failed to start recording on toggle-press: {e}", exc_info=True
                )
                # Reset state and attempt cleanup if start failed
                MenuIcon.set(app, MenuIcon.idle)
                STATE = "IDLE"
                # Attempt graceful stop to clean up recorder state if needed
                if recorder._stream:  # Check if stream was partially created
                    logger.warning("Attempting recorder cleanup after start failure...")
                    try:
                        await recorder.stop()
                    except Exception as stop_e:
                        logger.error(f"Error during cleanup recorder.stop: {stop_e}")
        elif STATE == "REC_TOGGLE":
            logger.info(
                ">>> Attempting to finish recording (Toggle Press REC_TOGGLE)..."
            )
            logger.info("Toggle key pressed again, initiating finish sequence.")
            await finish_recording(app)
            # state becomes busy then idle within finish_recording


# --- rumps application class ---


class WhisperFlow(rumps.App):
    """macos menu bar application class using rumps.

    integrates hotkey listening, state management, and ui updates.
    runs asyncio operations in a separate thread.
    """

    def __init__(self):
        """initializes the rumps app, queue timer, and asyncio thread setup."""
        super().__init__(MenuIcon.idle, quit_button=None)
        self.menu = ["Quit"]
        self.menu["Quit"].set_callback(self._quit_app)
        self.event_queue = hk_events()  # get the standard queue
        self.async_loop = None
        self.async_thread = None
        self.queue_timer = rumps.Timer(self.poll_queue, 0.05)  # poll queue every 50ms
        logger.info("WhisperFlow App initialized.")

    def poll_queue(self, _timer):
        """periodically called by rumps.timer to check the event queue.

        pulls events from the standard queue (populated by hotkeys.py)
        and schedules the async handler on the dedicated asyncio loop thread.
        """
        if not self.async_loop or not self.async_loop.is_running():
            # logger.debug("Async loop not ready, skipping queue poll.")
            return

        try:
            while not self.event_queue.empty():
                key_type, action = self.event_queue.get_nowait()
                logger.info(f"--- Polled event: type={key_type}, action={action} ---")
                # schedule handle_hotkey_event to run in the asyncio thread
                asyncio.run_coroutine_threadsafe(
                    handle_hotkey_event(self, key_type, action), self.async_loop
                )
                self.event_queue.task_done()
        except queue.Empty:
            pass  # no events in queue, normal
        except Exception as e:
            logger.error(
                f"Error polling queue or scheduling handler: {e}", exc_info=True
            )

    def _run_async_loop(self):
        """target function for the asyncio thread.
        sets up the event loop for the thread and runs it forever.
        """
        self.async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.async_loop)
        logger.info("Asyncio event loop starting in background thread.")
        self.async_loop.run_forever()
        # loop has stopped
        self.async_loop.close()
        logger.info("Asyncio event loop closed.")

    def _quit_app(self, _sender):
        """cleanly quits the application.
        stops the timer, signals the asyncio loop to stop, joins the thread.
        """
        logger.info("Quit menu item selected. Shutting down.")
        self.queue_timer.stop()  # stop polling
        logger.info("Queue timer stopped.")

        if self.async_loop and self.async_loop.is_running():
            logger.info("Requesting asyncio loop to stop...")
            self.async_loop.call_soon_threadsafe(self.async_loop.stop)
            # wait for the thread to finish
            if self.async_thread:
                logger.info("Waiting for asyncio thread to join...")
                self.async_thread.join(timeout=2.0)  # wait max 2 seconds
                if self.async_thread.is_alive():
                    logger.warning("Asyncio thread did not join cleanly.")
                else:
                    logger.info("Asyncio thread joined.")

        logger.info("Quitting rumps application.")
        rumps.quit_application()

    @objc.IBAction
    def reset_(self, sender):
        """resets the icon to the 'idle' state.

        called by the nstimer scheduled in ui.menuicon.success().
        needs to be an instance method accessible via objective-c.

        args:
            sender: the nstimer object (unused, but required by selector).
        """
        logger.debug("NSTimer fired: Resetting icon to idle.")
        MenuIcon.set(self, MenuIcon.idle)
        logger.info("UI State: Idle (🜏)")

    def run_loop(self):
        """starts the application's main run loop and background worker thread."""
        logger.info("Starting hotkey listener...")
        hotkeys_start()

        logger.info("Starting asyncio worker thread...")
        self.async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.async_thread.start()

        logger.info("Starting queue polling timer...")
        self.queue_timer.start()

        logger.info("Starting rumps application run loop...")
        super().run()  # blocks until quit
        logger.info("Rumps run loop finished.")


# --- entry point ---

if __name__ == "__main__":
    logger.info("Application starting...")
    app = WhisperFlow()
    # run_loop() handles starting the hotkey listener, worker, and rumps loop
    app.run_loop()
    logger.info("Application finished.")
