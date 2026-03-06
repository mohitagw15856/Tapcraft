"""Core engine: zone detection, gesture recognition, and event dispatch."""

import time
import threading
from typing import Callable

from tapcraft.config import VALID_ZONES, get_action


# Zone grid: maps normalized (x, y) coordinates to zone names
# Trackpad coordinates are normalized to 0.0 — 1.0
# x: left=0, right=1   y: top=0, bottom=1
ZONE_GRID = [
    ["top-left", "top-mid", "top-right"],
    ["mid-left", "center", "mid-right"],
    ["bot-left", "bot-mid", "bot-right"],
]


class TapEvent:
    """Represents a single detected tap on the trackpad."""

    def __init__(self, x: float, y: float, fingers: int = 1, timestamp: float = None):
        self.x = x  # 0.0 (left) to 1.0 (right)
        self.y = y  # 0.0 (top) to 1.0 (bottom)
        self.fingers = fingers
        self.timestamp = timestamp or time.time()

    def __repr__(self):
        return f"TapEvent(x={self.x:.2f}, y={self.y:.2f}, fingers={self.fingers})"


def detect_zone(x: float, y: float, padding: float = 0.05) -> str:
    """Map normalized trackpad coordinates to a zone name.

    Args:
        x: Horizontal position 0.0 (left) to 1.0 (right)
        y: Vertical position 0.0 (top) to 1.0 (bottom)
        padding: Dead zone between regions

    Returns:
        Zone name string, or "" if in a dead zone.
    """
    # Determine column (0, 1, 2)
    boundaries = [1 / 3, 2 / 3]

    def _bucket(val):
        for i, boundary in enumerate(boundaries):
            if val < boundary - padding:
                return i
            if val < boundary + padding:
                return -1  # dead zone
        return len(boundaries)

    col = _bucket(x)
    row = _bucket(y)

    if col == -1 or row == -1:
        return ""  # In dead zone

    return ZONE_GRID[row][col]


class GestureRecognizer:
    """Accumulates tap events and recognizes multi-tap gestures.

    Detects single, double, triple taps and multi-finger taps within
    a configurable time window.
    """

    def __init__(self, timeout_ms: int = 300, on_gesture: Callable = None):
        self.timeout_ms = timeout_ms
        self.on_gesture = on_gesture  # callback(zone, gesture_name, tap_events)

        self._pending_taps = []
        self._timer = None
        self._lock = threading.Lock()

    def feed(self, event: TapEvent):
        """Feed a new tap event into the recognizer."""
        with self._lock:
            # If pending taps exist, check if this tap is in the same zone
            if self._pending_taps:
                last = self._pending_taps[-1]
                time_delta = (event.timestamp - last.timestamp) * 1000

                # If too much time passed or different finger count, flush first
                if time_delta > self.timeout_ms or event.fingers != last.fingers:
                    self._flush_locked()

            self._pending_taps.append(event)

            # Reset the timer
            if self._timer:
                self._timer.cancel()

            self._timer = threading.Timer(
                self.timeout_ms / 1000.0, self._flush
            )
            self._timer.daemon = True
            self._timer.start()

    def _flush(self):
        """Timer callback — resolve pending taps into a gesture."""
        with self._lock:
            self._flush_locked()

    def _flush_locked(self):
        """Must be called while holding self._lock."""
        if not self._pending_taps:
            return

        taps = self._pending_taps.copy()
        self._pending_taps.clear()

        if self._timer:
            self._timer.cancel()
            self._timer = None

        # Determine gesture
        fingers = taps[0].fingers
        count = len(taps)

        # Use the average position for zone detection
        avg_x = sum(t.x for t in taps) / count
        avg_y = sum(t.y for t in taps) / count

        if fingers >= 3:
            gesture = "three-finger"
        elif fingers == 2:
            gesture = "two-finger"
        elif count >= 3:
            gesture = "triple"
        elif count == 2:
            gesture = "double"
        else:
            gesture = "single"

        if self.on_gesture:
            self.on_gesture(avg_x, avg_y, gesture, taps)


class TapCraftEngine:
    """Main engine that ties together zone detection, gesture recognition, and actions."""

    def __init__(self, config: dict, action_handler: Callable = None):
        self.config = config
        self.action_handler = action_handler
        self.running = False

        settings = config.get("settings", {})
        self.zone_padding = settings.get("zone_padding", 0.05)
        self.log_taps = settings.get("log_taps", False)
        self.feedback = settings.get("feedback", True)

        self.recognizer = GestureRecognizer(
            timeout_ms=settings.get("tap_timeout_ms", 300),
            on_gesture=self._on_gesture,
        )

        # Stats
        self.stats = {"total_taps": 0, "actions_triggered": 0}

    def handle_tap(self, event: TapEvent):
        """Called by platform listener when a tap is detected."""
        self.stats["total_taps"] += 1

        if self.log_taps:
            print(f"  [tap] {event}")

        self.recognizer.feed(event)

    def _on_gesture(self, x: float, y: float, gesture: str, taps: list):
        """Called when the gesture recognizer resolves a gesture."""
        zone = detect_zone(x, y, self.zone_padding)

        if not zone:
            if self.log_taps:
                print(f"  [zone] Dead zone — ignoring")
            return

        if self.log_taps:
            print(f"  [gesture] {zone} / {gesture} ({len(taps)} taps)")

        # Look up action
        action = get_action(self.config, zone, gesture)
        if action is None:
            if self.log_taps:
                print(f"  [action] No mapping for {zone}/{gesture}")
            return

        self.stats["actions_triggered"] += 1
        label = action.get("label", action["action"])
        print(f"🎯 {label} — [{zone} / {gesture}]")

        if self.action_handler:
            context = {
                "zone": zone,
                "gesture": gesture,
                "tap_count": len(taps),
                "fingers": taps[0].fingers,
                "x": x,
                "y": y,
                "timestamp": taps[-1].timestamp,
            }
            try:
                self.action_handler(action, context)
            except Exception as e:
                print(f"❌ Action error: {e}")

    def start(self):
        """Mark engine as running."""
        self.running = True
        print("🎯 TapCraft engine started — listening for taps...")

    def stop(self):
        """Stop the engine."""
        self.running = False
        print("\n🛑 TapCraft engine stopped.")
        print(f"   Total taps: {self.stats['total_taps']}")
        print(f"   Actions triggered: {self.stats['actions_triggered']}")
