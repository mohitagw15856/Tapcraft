"""Windows trackpad/input listener using pynput.

On Windows, raw multi-touch trackpad data requires the Precision Touchpad
(PTP) driver and WM_POINTER messages, which aren't accessible from Python
without a C extension. So we offer two practical approaches:

1. TRACKPAD MODE (default): Divides the screen into a 3x3 grid matching
   your trackpad. Taps/clicks on different screen regions trigger zone
   actions. This works because your cursor position roughly corresponds
   to where on the trackpad you're tapping.

2. HOTKEY MODE: Uses keyboard shortcuts (Ctrl+numpad) to trigger zones.
   Most reliable, works on any Windows machine.

Both modes detect click count (single/double/triple) automatically.
Right-click = two-finger, middle-click = three-finger.

Run as Administrator for best global input capture.
"""

import sys
import time
import threading

if sys.platform != "win32":
    raise ImportError("Windows listener only works on Windows")


def start_listener(engine):
    """Start the Windows input listener.

    Args:
        engine: TapCraftEngine instance to receive tap events.
    """
    try:
        from pynput import mouse, keyboard
    except ImportError:
        print("  Windows dependencies not installed.")
        print("  Run: pip install pynput")
        return

    import ctypes
    from tapcraft.core import TapEvent

    # Get screen dimensions
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()  # Handle DPI scaling
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
    except Exception:
        screen_w, screen_h = 1920, 1080

    print("  Windows listener starting...")
    print(f"  Screen: {screen_w}x{screen_h}")
    print()
    print("  HOW IT WORKS ON WINDOWS:")
    print("  Your screen is divided into a 3x3 grid matching the trackpad zones.")
    print("  Click/tap in different screen areas to trigger zone actions.")
    print("  Right-click = two-finger tap, Middle-click = three-finger tap.")
    print()
    print("  HOTKEY MODE (also active):")
    print("  Ctrl+Alt+Numpad 1-9 triggers zones directly:")
    print("    7=top-left  8=top-mid  9=top-right")
    print("    4=mid-left  5=center   6=mid-right")
    print("    1=bot-left  2=bot-mid  3=bot-right")
    print()
    print("  Listening... (Ctrl+C to stop)")
    print()

    # --- Click-based detection ---

    def on_click(x, y, button, pressed):
        """Handle mouse/trackpad click events."""
        if not pressed:
            return
        if not engine.running:
            return False

        # Normalize screen coordinates to 0-1 for zone mapping
        norm_x = max(0.0, min(1.0, x / screen_w))
        norm_y = max(0.0, min(1.0, y / screen_h))

        # Map button to finger count
        fingers = 1
        if button == mouse.Button.right:
            fingers = 2
        elif button == mouse.Button.middle:
            fingers = 3

        tap = TapEvent(x=norm_x, y=norm_y, fingers=fingers)
        engine.handle_tap(tap)

    # --- Hotkey-based zone triggers ---

    # Numpad mapping: matches the 3x3 grid visually
    # Numpad 7=top-left, 8=top-mid, 9=top-right
    # Numpad 4=mid-left, 5=center,  6=mid-right
    # Numpad 1=bot-left, 2=bot-mid, 3=bot-right
    NUMPAD_TO_ZONE = {
        keyboard.Key.num_lock: None,  # ignore
    }

    # Map numpad keys to (x, y) center coordinates for each zone
    NUMPAD_COORDS = {
        "7": (0.16, 0.16),  # top-left
        "8": (0.50, 0.16),  # top-mid
        "9": (0.83, 0.16),  # top-right
        "4": (0.16, 0.50),  # mid-left
        "5": (0.50, 0.50),  # center
        "6": (0.83, 0.50),  # mid-right
        "1": (0.16, 0.83),  # bot-left
        "2": (0.50, 0.83),  # bot-mid
        "3": (0.83, 0.83),  # bot-right
    }

    ctrl_pressed = False
    alt_pressed = False

    def on_key_press(key):
        nonlocal ctrl_pressed, alt_pressed

        if not engine.running:
            return False

        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            ctrl_pressed = True
            return
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            alt_pressed = True
            return

        # Ctrl+Alt+Numpad triggers zones
        if ctrl_pressed and alt_pressed:
            key_char = None

            # Handle numpad keys
            try:
                if hasattr(key, 'vk') and key.vk is not None:
                    # Numpad 0-9 have vk codes 96-105
                    if 96 <= key.vk <= 105:
                        key_char = str(key.vk - 96)
                    # Regular number keys 0-9 have vk codes 48-57
                    elif 48 <= key.vk <= 57:
                        key_char = str(key.vk - 48)
                elif hasattr(key, 'char') and key.char is not None:
                    key_char = key.char
            except AttributeError:
                pass

            if key_char and key_char in NUMPAD_COORDS:
                x, y = NUMPAD_COORDS[key_char]
                tap = TapEvent(x=x, y=y, fingers=1)
                engine.handle_tap(tap)

    def on_key_release(key):
        nonlocal ctrl_pressed, alt_pressed

        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            ctrl_pressed = False
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            alt_pressed = False

    # Start both listeners
    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener = keyboard.Listener(
        on_press=on_key_press,
        on_release=on_key_release,
    )

    mouse_listener.start()
    keyboard_listener.start()

    try:
        mouse_listener.join()
    except KeyboardInterrupt:
        mouse_listener.stop()
        keyboard_listener.stop()
        raise
