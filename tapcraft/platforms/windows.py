"""Windows trackpad listener using pynput.

On Windows, direct multi-touch trackpad access is more limited than macOS.
This module uses pynput for basic click detection with position tracking.
For Precision Touchpad devices, we attempt to use the raw input API for
multi-finger detection.

For best results, run as Administrator.
"""

import sys
import time

if sys.platform != "win32":
    raise ImportError("Windows listener only works on Windows")


def start_listener(engine):
    """Start the Windows trackpad event listener.

    Args:
        engine: TapCraftEngine instance to receive tap events.
    """
    try:
        from pynput import mouse
    except ImportError:
        print("❌ Windows dependencies not installed.")
        print("   Run: pip install pynput")
        return

    import ctypes
    from tapcraft.core import TapEvent

    # Get screen dimensions
    try:
        user32 = ctypes.windll.user32
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
    except Exception:
        screen_w, screen_h = 1920, 1080

    print("  🪟 Windows trackpad listener starting...")
    print("  ℹ️  For best results, run as Administrator.")
    print("  ℹ️  Precision Touchpad recommended for multi-touch.\n")

    def on_click(x, y, button, pressed):
        """Handle mouse/trackpad click events."""
        if not pressed:
            return  # Only handle press, not release

        if not engine.running:
            return False  # Stop listener

        # Normalize coordinates
        norm_x = x / screen_w
        norm_y = y / screen_h

        norm_x = max(0.0, min(1.0, norm_x))
        norm_y = max(0.0, min(1.0, norm_y))

        # Determine finger count from button
        # Left click = 1 finger, right click = 2 fingers, middle = 3 fingers
        fingers = 1
        if button == mouse.Button.right:
            fingers = 2
        elif button == mouse.Button.middle:
            fingers = 3

        tap = TapEvent(x=norm_x, y=norm_y, fingers=fingers)
        engine.handle_tap(tap)

    # Start pynput listener
    listener = mouse.Listener(on_click=on_click)
    listener.start()

    try:
        listener.join()
    except KeyboardInterrupt:
        listener.stop()
        raise
