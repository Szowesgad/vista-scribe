# hotkeys.py
#
# purpose: captures low-level keyboard events on macos to detect specific
#          hotkey presses (hold ctrl, toggle shift+cmd+/) without interfering
#          with standard input. provides an asynchronous queue for the main
#          application to consume these events.
#
# dependencies: quartz (coregraphics framework via pyobjc for event taps)
#               queue (for the event queue)
#
# key components: _tap function (callback for the quartz event tap)
#                 start function (sets up and enables the event tap)
#                 events function (returns the async queue)
#                 hold_vk, toggle_vk, toggle_fl (constants for key codes/flags)
#
# design rationale: uses a quartz event tap (cgeventtapcreate) for efficient,
#                   system-wide hotkey monitoring. this is preferred over
#                   higher-level libraries for monitoring specific modifier key
#                   states (like hold). an asyncio queue decouples event
#                   detection from event processing in the main application loop.
#
import Quartz
import queue
import logging
import os
import time

# --- constants ---

# Enable or disable hotkeys globally (can be overridden via env var)
HOTKEYS_ENABLED = os.environ.get("HOTKEYS_ENABLED", "1").lower() not in ("0", "false", "no", "off")

# Debug flag to control verbose event logging (set to False in production)
DEBUG = os.environ.get("HOTKEYS_DEBUG", "0").lower() in ("1", "true", "yes", "on")

# virtual key code for the 'hold' key (control)
# ref: /library/developer/commandlinetools/sdk/macosx.sdk/system/library/frameworks/carbon.framework/versions/a/frameworks/hisupport.framework/versions/a/headers/carbonprocessevents.h
# value based on standard virtual key codes, as quartz.kvk_control is unavailable directly
HOLD_VK = 59  # formerly quartz.kvk_control

# virtual key code for the 'toggle' key (/)
# value based on standard virtual key codes
TOGGLE_VK = 44  # formerly quartz.kvk_ansi_slash

# modifier flags for the 'toggle' shortcut (shift + command)
# combines flags using bitwise or
TOGGLE_FL = Quartz.kCGEventFlagMaskShift | Quartz.kCGEventFlagMaskCommand

# Option/Alt modifier mask
ALT_MASK = Quartz.kCGEventFlagMaskAlternate

# Double-tap Option timing (seconds); can be overridden via env var DOUBLE_OPTION_INTERVAL_MS
_DOUBLE_OPTION_INTERVAL = float(os.environ.get("DOUBLE_OPTION_INTERVAL_MS", "350")) / 1000.0

# --- state ---

# Get a logger for this module
logger = logging.getLogger(__name__)

# async queue to send detected hotkey events to the main application loop
# maxsize=0 means unlimited size
_queue = queue.Queue()
_last_hold_state = None  # track the last state of the ctrl key (true=down, false=up)
_last_alt_state = None   # track the last state of the option/alt key
_last_alt_down_ts = 0.0  # timestamp of last alt down event

# Store references to active event taps for proper cleanup
_active_tap = None
_run_loop_source = None
_is_tap_active = False

# --- public api ---


def events():
    """Returns the standard queue used for hotkey events.

    Returns:
        queue.Queue: The queue instance.
    """
    return _queue


def is_active():
    """Returns whether hotkeys are currently active.
    
    Returns:
        bool: True if hotkeys are enabled and the event tap is active.
    """
    global _is_tap_active
    return HOTKEYS_ENABLED and _is_tap_active


def start():
    """Creates and enables the Quartz event tap.

    Sets up the tap to listen for keydown and keyup events globally,
    registers the _tap callback, adds it to the current run loop,
    and enables the tap.
    
    Returns:
        bool: True if initialization succeeded, False on failure.
    """
    global _active_tap, _run_loop_source, _is_tap_active
    
    # Skip initialization if hotkeys are globally disabled
    if not HOTKEYS_ENABLED:
        logger.info("Hotkeys are disabled via HOTKEYS_ENABLED. Skipping initialization.")
        return False
    
    # Check if already initialized
    if _is_tap_active:
        logger.warning("Event tap is already active. Ignoring duplicate start() call.")
        return True
    
    # Reset any previous state
    stop()
    
    try:
        # Create the event mask for the keys we want to monitor
        event_mask = (
            Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)
            | Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp)
            | Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged)
        )
        
        # Create the event tap
        _active_tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap,
            Quartz.kCGHeadInsertEventTap,
            0,
            event_mask,
            _tap,
            None,
        )

        if not _active_tap:
            logger.error("Failed to create event tap. Ensure accessibility permissions are granted.")
            # When running in nohup/background, make sure to clean up before returning
            stop()
            return False

        # Create a run loop source from the event tap
        _run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, _active_tap, 0)

        # Add the source to the current run loop for monitoring
        Quartz.CFRunLoopAddSource(
            Quartz.CFRunLoopGetCurrent(), _run_loop_source, Quartz.kCFRunLoopCommonModes
        )

        # Enable the event tap
        Quartz.CGEventTapEnable(_active_tap, True)
        
        _is_tap_active = True
        logger.info("Event tap started successfully.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize hotkeys: {e}")
        # Clean up any partially initialized resources
        stop()
        return False


def stop():
    """Safely disables and cleans up the event tap.
    
    This function should be called when shutting down the application
    or when hotkeys need to be temporarily disabled.
    
    Returns:
        bool: True if cleanup succeeded, False otherwise.
    """
    global _active_tap, _run_loop_source, _is_tap_active
    
    try:
        if _active_tap:
            Quartz.CGEventTapEnable(_active_tap, False)
            # Note: We don't release the CFMachPort here because it can lead to crashes
            # The OS will clean it up when the process exits
        
        if _run_loop_source:
            try:
                Quartz.CFRunLoopRemoveSource(
                    Quartz.CFRunLoopGetCurrent(), 
                    _run_loop_source, 
                    Quartz.kCFRunLoopCommonModes
                )
            except Exception:
                # Ignore errors during cleanup
                pass
            
        _is_tap_active = False
        _active_tap = None
        _run_loop_source = None
        
        logger.info("Event tap stopped and resources released.")
        return True
    except Exception as e:
        logger.exception(f"Error stopping event tap: {e}")
        return False


# --- private functions ---


def _tap(proxy, type_, event, refcon):
    """Quartz event tap callback function.

    This function is called by the system for each tapped keyboard event.
    It checks if the event matches the defined hotkeys (hold or toggle)
    and puts a corresponding event tuple into the async queue.

    Args:
        proxy: The event tap proxy.
        type_: The type of the event (e.g., kCGEventKeyDown, kCGEventKeyUp).
        event: The CGEvent object.
        refcon: User-defined data passed to CGEventTapCreate (None in this case).

    Returns:
        CGEvent: The original or a modified event. Must return the event
                to allow it to pass through, or None to block it.
    """
    # Get key information
    try:
        keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
        flags = Quartz.CGEventGetFlags(event)
    except Exception as e:
        logger.error(f"Error getting event data: {e}")
        return event  # pass the event through on error

    # Debug logging (only when DEBUG is enabled)
    if DEBUG:
        event_type_str = "Unknown"
        if type_ == Quartz.kCGEventKeyDown:
            event_type_str = "KeyDown"
        elif type_ == Quartz.kCGEventKeyUp:
            event_type_str = "KeyUp"
        elif type_ == Quartz.kCGEventFlagsChanged:
            event_type_str = "FlagsChanged"
        logger.debug(f"Key: {keycode}, Flags: {flags}, Type: {event_type_str}")

    try:
        # Check for 'hold' key (ctrl) and Option double-tap via flags changes
        if type_ == Quartz.kCGEventFlagsChanged:
            # Determine current ctrl and alt states directly from flags
            ctrl_is_down = (flags & Quartz.kCGEventFlagMaskControl) != 0
            alt_is_down = (flags & ALT_MASK) != 0

            # Ctrl hold down/up events
            global _last_hold_state
            if ctrl_is_down != _last_hold_state:
                event_action = "down" if ctrl_is_down else "up"
                _queue.put(("hold", event_action))
                _last_hold_state = ctrl_is_down  # Update the tracked state
                logger.info(f"Hotkey: Hold {event_action} (Ctrl key)")

            # Option double-tap detection: look for two down edges within interval
            global _last_alt_state, _last_alt_down_ts
            if alt_is_down != _last_alt_state:
                # Edge detected
                now = time.perf_counter()
                if alt_is_down:
                    # This is a down edge; check time since previous down
                    if _last_alt_down_ts and (now - _last_alt_down_ts) <= _DOUBLE_OPTION_INTERVAL:
                        # Double tap detected -> emit toggle press
                        _queue.put(("toggle", "press"))
                        logger.info("Hotkey: Toggle press (Double Option)")
                        _last_alt_down_ts = 0.0  # Reset window
                    else:
                        _last_alt_down_ts = now
                _last_alt_state = alt_is_down

        # Check for classic 'toggle' key (shift+cmd+/) - only on key down
        elif type_ == Quartz.kCGEventKeyDown and keycode == TOGGLE_VK:
            # Using `(flags & TOGGLE_FL) == TOGGLE_FL` checks if *at least* shift and command are pressed
            if (flags & TOGGLE_FL) == TOGGLE_FL:
                _queue.put(("toggle", "press"))
                logger.info("Hotkey: Toggle press (Shift+Cmd+/)")

    except Exception as e:
        # Log error but don't block the event to avoid freezing keyboard
        logger.error(f"Error in event tap callback: {e}")
        
    # Return the event unmodified to allow it to pass to the active application
    return event
