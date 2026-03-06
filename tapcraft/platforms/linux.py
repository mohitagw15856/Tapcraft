"""Linux trackpad listener using evdev.

This module reads raw input events from the trackpad device via the
Linux input subsystem (evdev). It supports multi-touch tracking for
devices that report MT (multi-touch) protocol events.

Requirements:
- python-evdev package
- User must be in the 'input' group: sudo usermod -aG input $USER
- Or run with sudo (not recommended for daily use)
"""

import sys
import os
import time

if sys.platform != "linux":
    raise ImportError("Linux listener only works on Linux")


def find_trackpad_device():
    """Find the trackpad input device."""
    try:
        import evdev
    except ImportError:
        return None

    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

    # Look for touchpad devices
    touchpad_keywords = ["touchpad", "trackpad", "synaptics", "elan", "alps"]

    for device in devices:
        name_lower = device.name.lower()
        if any(keyword in name_lower for keyword in touchpad_keywords):
            return device

    # Fallback: look for devices with ABS_MT_POSITION_X capability
    for device in devices:
        caps = device.capabilities(verbose=True)
        abs_caps = caps.get(('EV_ABS', 3), [])
        for cap_name, _ in abs_caps:
            if 'ABS_MT_POSITION_X' in str(cap_name):
                return device

    return None


def start_listener(engine):
    """Start the Linux trackpad event listener.

    Args:
        engine: TapCraftEngine instance to receive tap events.
    """
    try:
        import evdev
        from evdev import ecodes
    except ImportError:
        print("❌ Linux dependencies not installed.")
        print("   Run: pip install evdev")
        return

    from tapcraft.core import TapEvent

    device = find_trackpad_device()
    if device is None:
        print("❌ No trackpad device found.")
        print("   Make sure you're in the 'input' group:")
        print("   sudo usermod -aG input $USER")
        print("   Then log out and back in.")
        return

    print(f"  🐧 Linux trackpad listener starting...")
    print(f"  📱 Device: {device.name} ({device.path})")

    # Get trackpad dimensions for normalization
    abs_info = device.capabilities(absinfo=True).get(ecodes.EV_ABS, [])
    x_info = None
    y_info = None

    for code, info in abs_info:
        if code == ecodes.ABS_MT_POSITION_X or code == ecodes.ABS_X:
            x_info = info
        elif code == ecodes.ABS_MT_POSITION_Y or code == ecodes.ABS_Y:
            y_info = info

    if not x_info or not y_info:
        print("  ⚠️  Could not determine trackpad dimensions")
        x_min, x_max = 0, 1000
        y_min, y_max = 0, 600
    else:
        x_min, x_max = x_info.min, x_info.max
        y_min, y_max = y_info.min, y_info.max

    print(f"  📐 Range: X({x_min}-{x_max}), Y({y_min}-{y_max})\n")

    # Track multi-touch slots
    current_slot = 0
    slots = {}  # slot_id -> {x, y, tracking_id}
    touch_start_time = {}

    BTN_TOUCH = ecodes.BTN_TOUCH
    BTN_TOOL_FINGER = getattr(ecodes, "BTN_TOOL_FINGER", 0x145)
    BTN_TOOL_DOUBLETAP = getattr(ecodes, "BTN_TOOL_DOUBLETAP", 0x14d)
    BTN_TOOL_TRIPLETAP = getattr(ecodes, "BTN_TOOL_TRIPLETAP", 0x14e)

    finger_count = 1

    try:
        for event in device.read_loop():
            if not engine.running:
                break

            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_MT_SLOT:
                    current_slot = event.value
                elif event.code == ecodes.ABS_MT_TRACKING_ID:
                    if event.value == -1:
                        # Finger lifted
                        if current_slot in slots:
                            slot = slots[current_slot]
                            start_t = touch_start_time.get(current_slot, 0)
                            duration = time.time() - start_t

                            # Only count as tap if short duration (not drag)
                            if duration < 0.3:
                                norm_x = (slot.get("x", 0) - x_min) / (x_max - x_min)
                                norm_y = (slot.get("y", 0) - y_min) / (y_max - y_min)
                                norm_x = max(0.0, min(1.0, norm_x))
                                norm_y = max(0.0, min(1.0, norm_y))

                                tap = TapEvent(
                                    x=norm_x, y=norm_y,
                                    fingers=finger_count
                                )
                                engine.handle_tap(tap)

                            del slots[current_slot]
                            touch_start_time.pop(current_slot, None)
                    else:
                        # New finger touching
                        slots[current_slot] = {"x": 0, "y": 0}
                        touch_start_time[current_slot] = time.time()

                elif event.code == ecodes.ABS_MT_POSITION_X:
                    if current_slot in slots:
                        slots[current_slot]["x"] = event.value
                elif event.code == ecodes.ABS_MT_POSITION_Y:
                    if current_slot in slots:
                        slots[current_slot]["y"] = event.value

            elif event.type == ecodes.EV_KEY:
                # Track finger count from BTN_TOOL events
                if event.code == BTN_TOOL_TRIPLETAP and event.value == 1:
                    finger_count = 3
                elif event.code == BTN_TOOL_DOUBLETAP and event.value == 1:
                    finger_count = 2
                elif event.code == BTN_TOOL_FINGER and event.value == 1:
                    finger_count = 1

    except KeyboardInterrupt:
        raise
    except PermissionError:
        print("❌ Permission denied reading trackpad device.")
        print("   Add yourself to the input group:")
        print("   sudo usermod -aG input $USER")
        print("   Then log out and back in.")
    except Exception as e:
        print(f"❌ Listener error: {e}")
