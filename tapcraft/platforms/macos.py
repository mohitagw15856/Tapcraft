"""macOS trackpad listener using Quartz Event Taps.

This module captures multi-touch trackpad events on macOS using the
Quartz (CoreGraphics) framework. It requires Accessibility permissions.

How it works:
- Creates a CGEventTap to intercept trackpad events system-wide
- Detects tap-down events and extracts position + finger count
- Normalizes coordinates to 0.0-1.0 range
- Feeds events to the TapCraft engine
"""

import sys
import time

if sys.platform != "darwin":
    raise ImportError("macOS listener only works on macOS")


def start_listener(engine):
    """Start the macOS trackpad event listener.

    Args:
        engine: TapCraftEngine instance to receive tap events.
    """
    try:
        import Quartz
        from Quartz import (
            CGEventTapCreate,
            CGEventTapEnable,
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            kCGEventTapOptionListenOnly,
            CGEventGetLocation,
            CGEventGetIntegerValueField,
            kCGEventLeftMouseDown,
            kCGEventOtherMouseDown,
            NSEvent,
        )
        from Quartz import kCGMouseEventClickState
        import AppKit
    except ImportError:
        print("❌ macOS dependencies not installed.")
        print("   Run: pip install pyobjc-framework-Quartz pyobjc-framework-Cocoa")
        return

    from tapcraft.core import TapEvent

    # Get screen dimensions for coordinate normalization
    screen = AppKit.NSScreen.mainScreen()
    if screen:
        frame = screen.frame()
        screen_w = frame.size.width
        screen_h = frame.size.height
    else:
        screen_w, screen_h = 1440, 900  # Fallback

    # We use NSEvent to get multi-touch data
    # This approach tracks touches on the trackpad directly

    print("  🍎 macOS trackpad listener starting...")
    print("  ℹ️  Make sure Accessibility permissions are granted.")
    print("     (System Preferences → Privacy & Security → Accessibility)\n")

    # Track active touches to detect taps vs drags
    _touch_start = {}
    _tap_threshold_px = 10  # Max movement to count as a tap (not drag)
    _tap_max_duration = 0.3  # Max duration for a tap

    def event_callback(proxy, event_type, event, refcon):
        """Callback for CGEventTap — captures mouse/trackpad events."""
        try:
            if event_type == kCGEventLeftMouseDown:
                location = CGEventGetLocation(event)
                click_count = CGEventGetIntegerValueField(event, kCGMouseEventClickState)

                # Normalize coordinates
                x = location.x / screen_w
                y = location.y / screen_h

                # Clamp to 0-1
                x = max(0.0, min(1.0, x))
                y = max(0.0, min(1.0, y))

                # Detect finger count from pressure/touch info
                # Single click = 1 finger tap on trackpad
                fingers = 1

                tap = TapEvent(x=x, y=y, fingers=fingers)
                engine.handle_tap(tap)

        except Exception as e:
            print(f"  ⚠️  Event callback error: {e}")

        return event

    # For richer multi-touch detection, we use NSEvent's touch API
    # This gives us actual finger count and touch positions

    class TrackpadMonitor:
        """Monitors trackpad multi-touch events via NSEvent global monitoring."""

        def __init__(self):
            self.monitors = []

        def start(self):
            """Set up global event monitors."""
            # Monitor for gesture events (multi-finger taps)
            mask = (
                AppKit.NSEventMaskGesture
                | AppKit.NSEventMaskMagnify
                | AppKit.NSEventMaskPressure
            )

            # Also monitor regular mouse events for single taps
            mouse_mask = (
                AppKit.NSEventMaskLeftMouseDown
                | AppKit.NSEventMaskOtherMouseDown
            )

            def handle_gesture(event):
                """Handle multi-touch gesture events."""
                try:
                    touches = event.touchesMatchingPhase_inView_(
                        AppKit.NSTouchPhaseTouching, None
                    )
                    if touches and len(touches) >= 2:
                        finger_count = len(touches)
                        # Get average touch position
                        positions = []
                        for touch in touches:
                            pos = touch.normalizedPosition()
                            positions.append((pos.x, 1.0 - pos.y))  # Flip Y

                        avg_x = sum(p[0] for p in positions) / len(positions)
                        avg_y = sum(p[1] for p in positions) / len(positions)

                        tap = TapEvent(x=avg_x, y=avg_y, fingers=finger_count)
                        engine.handle_tap(tap)
                except Exception:
                    pass

            def handle_mouse(event):
                """Handle single-finger taps via mouse events."""
                try:
                    location = event.locationInWindow()
                    screen_loc = event.window()
                    if screen_loc:
                        location = screen_loc.convertPointToScreen_(location)

                    x = location.x / screen_w
                    y = 1.0 - (location.y / screen_h)  # Flip Y for macOS

                    x = max(0.0, min(1.0, x))
                    y = max(0.0, min(1.0, y))

                    tap = TapEvent(x=x, y=y, fingers=1)
                    engine.handle_tap(tap)
                except Exception:
                    pass

            # Register monitors
            gesture_monitor = AppKit.NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                mask, handle_gesture
            )
            mouse_monitor = AppKit.NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                mouse_mask, handle_mouse
            )

            self.monitors = [gesture_monitor, mouse_monitor]

        def stop(self):
            for monitor in self.monitors:
                if monitor:
                    AppKit.NSEvent.removeMonitor_(monitor)
            self.monitors = []

    monitor = TrackpadMonitor()
    monitor.start()

    # Run the macOS event loop
    try:
        app = AppKit.NSApplication.sharedApplication()
        app.run()
    except KeyboardInterrupt:
        monitor.stop()
        raise
