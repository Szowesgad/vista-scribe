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

# --- constants ---

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
import os, time
_DOUBLE_OPTION_INTERVAL = float(os.environ.get("DOUBLE_OPTION_INTERVAL_MS", "350")) / 1000.0

# --- state ---

# async queue to send detected hotkey events to the main application loop
# maxsize=0 means unlimited size
_queue = queue.Queue()
_last_hold_state = None  # track the last state of the ctrl key (true=down, false=up)
_last_alt_state = None   # track the last state of the option/alt key
_last_alt_down_ts = 0.0  # timestamp of last alt down event

# --- public api ---


def events():
    """returns the standard queue used for hotkey events.

    returns:
        queue.queue: the queue instance.
    """
    return _queue


def start():
    """creates and enables the quartz event tap.

    sets up the tap to listen for keydown and keyup events globally,
    registers the _tap callback, adds it to the current run loop,
    and enables the tap.
    this function should be called once at application startup.
    """
    # create an event tap.
    # kCGSessionEventTap: specifies the tap location (session-wide events).
    # kCGHeadInsertEventTap: specifies tap placement (start of the event stream).
    # 0: specifies tap options (Quartz.kCGEventTapOptionDefault).
    # CGEventMaskBit(kCGEventKeyDown)|CGEventMaskBit(kCGEventKeyUp)|CGEventMaskBit(kCGEventFlagsChanged): specifies events to tap (key down, key up, and flags changed).
    # _tap: the callback function.
    # none: user-defined data (not needed here).
    event_mask = (
        Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown)
        | Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp)
        | Quartz.CGEventMaskBit(Quartz.kCGEventFlagsChanged)
    )
    tap = Quartz.CGEventTapCreate(
        Quartz.kCGSessionEventTap,
        Quartz.kCGHeadInsertEventTap,
        0,
        event_mask,
        _tap,
        None,
    )

    if not tap:
        print(
            "Error: Failed to create event tap. Ensure accessibility permissions are granted."
        )
        # consider raising an exception or exiting gracefully
        return

    # create a run loop source from the event tap.
    runLoopSource = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)

    # add the source to the current run loop for monitoring.
    Quartz.CFRunLoopAddSource(
        Quartz.CFRunLoopGetCurrent(), runLoopSource, Quartz.kCFRunLoopCommonModes
    )

    # enable the event tap.
    Quartz.CGEventTapEnable(tap, True)

    print("Event tap started successfully.")


# --- private functions ---


def _tap(proxy, type_, event, refcon):
    """quartz event tap callback function.

    this function is called by the system for each tapped keyboard event.
    it checks if the event matches the defined hotkeys (hold or toggle)
    and puts a corresponding event tuple into the async queue.

    args:
        proxy: the event tap proxy.
        type_: the type of the event (e.g., kCGEventKeyDown, kCGEventKeyUp).
        event: the cgevent object.
        refcon: user-defined data passed to CGEventTapCreate (none in this case).

    returns:
        cgevent: the original or a modified event. must return the event
                 to allow it to pass through, or none to block it.
    """
    global _last_hold_state  # make sure we modify the global variable
    keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
    flags = Quartz.CGEventGetFlags(event)

    # --- debug: log all events ---
    event_type_str = "Unknown"
    if type_ == Quartz.kCGEventKeyDown:
        event_type_str = "KeyDown"
    elif type_ == Quartz.kCGEventKeyUp:
        event_type_str = "KeyUp"
    elif type_ == Quartz.kCGEventFlagsChanged:
        event_type_str = "FlagsChanged"
    print(f"[Tap Callback] Key: {keycode}, Flags: {flags}, Type: {event_type_str}")
    # --- end debug ---

    # check for 'hold' key (ctrl) and Option double-tap via flags changes
    if type_ == Quartz.kCGEventFlagsChanged:
        # determine current ctrl and alt states directly from flags
        ctrl_is_down = (flags & Quartz.kCGEventFlagMaskControl) != 0
        alt_is_down = (flags & ALT_MASK) != 0

        # Ctrl hold down/up events
        if ctrl_is_down != _last_hold_state:
            event_action = "down" if ctrl_is_down else "up"
            _queue.put(("hold", event_action))
            _last_hold_state = ctrl_is_down  # update the tracked state
            print(f"** Queued Hold Event: {event_action} (Ctrl state changed) **")

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
                    print("** Queued Toggle Event: press (Double Option) **")
                    _last_alt_down_ts = 0.0  # reset window
                else:
                    _last_alt_down_ts = now
            _last_alt_state = alt_is_down

    # check for classic 'toggle' key (shift+cmd+/) - only on key down
    elif type_ == Quartz.kCGEventKeyDown and keycode == TOGGLE_VK:
        # using `(flags & TOGGLE_FL) == TOGGLE_FL` checks if *at least* shift and command are pressed.
        if (flags & TOGGLE_FL) == TOGGLE_FL:
            _queue.put(("toggle", "press"))
            print("** Queued Toggle Event: press **")  # debug confirmation

    # return the event unmodified to allow it to pass to the active application.
    return event
