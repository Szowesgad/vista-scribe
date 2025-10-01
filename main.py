# main.py
#
# purpose: entry point for the vista-scribe application. initializes and runs the
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
# key components: vista-scribe class (subclass of rumps.app)
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
import sys
import objc  # for selector
import threading  # for asyncio thread
import queue  # for checking standard queue

# import our modules
from hotkeys import start as hotkeys_start, stop as hotkeys_stop, is_active as hotkeys_active, events as hk_events
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


class VistaScribe(rumps.App):
    """macOS menu bar application class using rumps.

    Integrates hotkey listening, state management, and UI updates.
    Runs asyncio operations in a separate thread.
    """

    def __init__(self):
        """Initializes the rumps app, queue timer, and asyncio thread setup."""
        super().__init__(MenuIcon.idle, quit_button=None)

        # Try to set a tray icon image (keeps state glyphs out of the title area)
        try:
            from path_utils import normalize_model_path  # lazy import to avoid cycles

            icon_env = os.environ.get("TRAY_ICON")
            repo_root = os.path.dirname(os.path.abspath(__file__))
            default_icon = os.path.join(repo_root, "assets", "icon.png")
            candidate = icon_env or default_icon
            if candidate:
                # Normalize '/Users' → '/users' on macOS when that path exists
                norm = normalize_model_path(candidate) or candidate
                if os.path.isfile(norm):
                    self.icon = norm
                    # Hide title text when an icon is present
                    self.title = ""
                    logger.info(f"Tray icon set: {norm}")
        except Exception as e:
            logger.warning(f"Tray icon setup skipped: {e}")
        
        # Initialize menu with app status and controls
        self.hotkeys_enabled = True  # Default state, will be updated in run_loop
        
        self.menu = [
            "Status: Initializing...",
            None,  # Separator
            "Enable Hotkeys",
            "Open System Accessibility Settings...",
            None,  # Separator
            "Quit"
        ]
        
        # Set callbacks
        self.menu["Enable Hotkeys"].set_callback(self._toggle_hotkeys)
        self.menu["Open System Accessibility Settings..."].set_callback(self._open_accessibility)
        self.menu["Quit"].set_callback(self._quit_app)
        
        # Disable menu items initially until we know hotkeys status
        self.menu["Enable Hotkeys"].state = False
        
        self.event_queue = hk_events()  # get the standard queue
        self.async_loop = None
        self.async_thread = None
        self.queue_timer = rumps.Timer(self.poll_queue, 0.05)  # poll queue every 50ms
        logger.info("Vista Scribe App initialized.")

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
        """Cleanly quits the application.
        
        Stops hotkeys, cleans up event taps, stops the timer, 
        signals the asyncio loop to stop, joins the thread.
        """
        logger.info("Quit menu item selected. Shutting down.")
        
        # First, safely stop any active hotkey event taps
        logger.info("Cleaning up hotkey event taps...")
        try:
            hotkeys_stop()
            logger.info("Hotkey event taps disabled successfully")
        except Exception as e:
            logger.error(f"Error disabling hotkey event taps: {e}")
        
        # Stop the queue polling timer
        self.queue_timer.stop()
        logger.info("Queue timer stopped.")

        # Clean up the asyncio thread
        if self.async_loop and self.async_loop.is_running():
            logger.info("Requesting asyncio loop to stop...")
            self.async_loop.call_soon_threadsafe(self.async_loop.stop)
            # Wait for the thread to finish
            if self.async_thread:
                logger.info("Waiting for asyncio thread to join...")
                self.async_thread.join(timeout=2.0)  # Wait max 2 seconds
                if self.async_thread.is_alive():
                    logger.warning("Asyncio thread did not join cleanly.")
                else:
                    logger.info("Asyncio thread joined.")

        logger.info("Quitting rumps application.")
        rumps.quit_application()

    def _toggle_hotkeys(self, sender):
        """Toggle hotkeys on/off based on current state.
        
        When toggled off, stops the event tap. When toggled on, 
        attempts to restart the hotkey listeners.
        """
        if self.hotkeys_enabled:
            # Disable hotkeys
            logger.info("Disabling hotkeys by user request")
            hotkeys_stop()
            self.hotkeys_enabled = False
            self.menu["Enable Hotkeys"].state = False
            self.menu["Status: Hotkeys Enabled"].title = "Status: Hotkeys Disabled"
            # Update icon to show disabled state
            MenuIcon.set(self, "🚫")
        else:
            # Enable hotkeys
            logger.info("Enabling hotkeys by user request")
            if hotkeys_start():
                self.hotkeys_enabled = True
                self.menu["Enable Hotkeys"].state = True
                self.menu["Status: Hotkeys Disabled"].title = "Status: Hotkeys Enabled"
                # Reset icon to idle state
                MenuIcon.set(self, MenuIcon.idle)
            else:
                # Failed to enable
                logger.error("Failed to enable hotkeys. Check accessibility permissions.")
                # Show error in menu
                self.menu["Status: Hotkeys Disabled"].title = "Status: Failed to Enable Hotkeys"
                # Show error dialog
                rumps.alert(
                    title="Hotkey Initialization Failed",
                    message="Could not enable hotkeys. Please check Accessibility permissions in System Settings.",
                    ok="OK"
                )
    
    def _open_accessibility(self, sender):
        """Open macOS System Settings to the Accessibility pane.
        
        This helps users grant the necessary permissions for hotkeys to work.
        """
        try:
            # Use AppleScript to open the Privacy & Security settings
            import subprocess
            script = """
            tell application "System Settings"
                activate
                reveal anchor "Privacy_Accessibility" of pane id "com.apple.settings.PrivacySecurity.extension"
            end tell
            """
            subprocess.run(["osascript", "-e", script])
            logger.info("Opened System Settings to Accessibility pane")
        except Exception as e:
            logger.error(f"Failed to open Accessibility settings: {e}")
            rumps.alert(
                title="Could Not Open Settings",
                message="Please open System Settings → Privacy & Security → Accessibility manually and enable this app.",
                ok="OK"
            )

    @objc.IBAction
    def reset_(self, sender):
        """Resets the icon to the 'idle' state.

        Called by the NSTimer scheduled in ui.menuicon.success().
        Needs to be an instance method accessible via Objective-C.

        Args:
            sender: The NSTimer object (unused, but required by selector).
        """
        logger.debug("NSTimer fired: Resetting icon to idle.")
        # Only reset to idle if hotkeys are enabled
        if self.hotkeys_enabled:
            MenuIcon.set(self, MenuIcon.idle)
            logger.info("UI State: Idle (🜏)")
        else:
            # Keep showing disabled state
            MenuIcon.set(self, "🚫")
            logger.info("UI State: Hotkeys disabled (🚫)")

    def run_loop(self):
        """Starts the application's main run loop and background worker thread.
        
        Handles hotkey initialization failures gracefully, providing user feedback
        and allowing the app to run in a degraded mode without hotkeys if needed.
        
        In nohup/background mode, avoids showing user dialogs that would block execution.
        """
        # Check if running in background/nohup mode
        # Multiple methods to detect background mode for robustness
        is_background_mode = False
        
        # Method 1: Explicit environment variable
        if os.environ.get("NOHUP_MODE", "0").lower() in ("1", "true", "yes", "on"):
            is_background_mode = True
            logger.info("Background mode detected via NOHUP_MODE environment variable")
        
        # Method 2: Check if stdout is redirected (common with nohup)
        try:
            if not os.isatty(sys.stdout.fileno()):
                is_background_mode = True
                logger.info("Background mode detected: stdout is not a TTY")
        except (AttributeError, OSError):
            # If we can't check isatty (could be redirected)
            pass
            
        # Method 3: Check parent process name (often 'nohup')
        try:
            import psutil
            try:
                parent = psutil.Process(os.getppid())
                if parent.name() in ('nohup', 'daemondo', 'launchd'):
                    is_background_mode = True
                    logger.info(f"Background mode detected: parent process is {parent.name()}")
            except Exception as e:
                logger.warning(f"Could not check parent process: {e}")
        except ImportError:
            # psutil not available
            logger.info("psutil not available, skipping parent process check")
            pass
        
        logger.info(f"Running in {'background' if is_background_mode else 'interactive'} mode")
        
        # Initialize hotkeys with proper error handling
        logger.info("Starting hotkey listener...")
        hotkeys_success = hotkeys_start()
        
        # Update UI based on hotkey initialization result
        if hotkeys_success:
            logger.info("Hotkeys initialized successfully")
            self.hotkeys_enabled = True
            self.menu["Status: Initializing..."].title = "Status: Hotkeys Enabled"
            self.menu["Enable Hotkeys"].state = True
        else:
            logger.error("Failed to initialize hotkeys. App will run without keyboard shortcuts.")
            self.hotkeys_enabled = False
            self.menu["Status: Initializing..."].title = "Status: Hotkeys Disabled"
            self.menu["Enable Hotkeys"].state = False
            
            # Show visual indication of disabled hotkeys
            MenuIcon.set(self, "🚫")
            
            # In background mode, don't show dialogs that would block execution
            if not is_background_mode:
                # Only show alert dialog when not in background mode
                try:
                    rumps.alert(
                        title="Hotkey Initialization Failed",
                        message=(
                            "Vista Scribe could not initialize keyboard shortcuts due to missing permissions.\n\n"
                            "The app will continue to run, but keyboard shortcuts (Ctrl hold, ⇧⌘/, and double-Option) "
                            "will not work until permissions are granted.\n\n"
                            "To enable hotkeys, click 'Open System Accessibility Settings...' in the menu, "
                            "add this application to the allowed apps list, and then use 'Enable Hotkeys' from the menu."
                        ),
                        ok="OK"
                    )
                except Exception as e:
                    logger.error(f"Failed to show alert dialog: {e}")
            else:
                logger.info("Running in background mode - skipping alert dialogs")
                
        # Release event tap resources if hotkeys failed to initialize
        if not hotkeys_success:
            logger.info("Event tap stopped and resources released.")

        # Start the async thread for background processing
        logger.info("Starting asyncio worker thread...")
        self.async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.async_thread.start()

        # Only start queue polling if hotkeys are enabled
        if self.hotkeys_enabled:
            logger.info("Starting queue polling timer...")
            self.queue_timer.start()
        else:
            logger.info("Skipping queue polling timer (hotkeys disabled)")

        # Start the rumps application
        logger.info("Starting rumps application run loop...")
        super().run()  # blocks until quit
        logger.info("Rumps run loop finished.")


# --- entry point ---

if __name__ == "__main__":
    logger.info("Application starting...")
    app = VistaScribe()
    # run_loop() handles starting the hotkey listener, worker, and rumps loop
    app.run_loop()
    logger.info("Application finished.")
