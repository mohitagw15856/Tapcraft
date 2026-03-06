"""Slap detection engine — connects impact detection to configurable actions.

This module bridges the hardware-level slap detection (accelerometer or
microphone) with the TapCraft action system. It supports:

- Strength-based action mapping (light/medium/hard/brutal)
- Escalation mode (more slaps = more intense responses)
- Auto-detection of the best available sensor
"""

import sys
import time
import threading
from collections import deque
from typing import Callable, Optional

from tapcraft.actions import execute_action


VALID_STRENGTHS = ["light", "medium", "hard", "brutal", "any"]


class EscalationTracker:
    """Tracks slap frequency for escalation mode.

    Maintains a rolling window of slap timestamps and determines
    the current escalation level based on slap count.
    """

    def __init__(self, window_minutes: float = 5.0, levels: list = None):
        self.window_seconds = window_minutes * 60
        self.levels = levels or []
        self._timestamps = deque()

        # Sort levels by count ascending
        self.levels.sort(key=lambda l: l.get("count", 0))

    def record_slap(self) -> Optional[dict]:
        """Record a slap and return the current escalation level action (if any)."""
        now = time.time()
        self._timestamps.append(now)

        # Remove old timestamps outside the window
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

        count = len(self._timestamps)

        # Find the highest matching level
        matched_level = None
        for level in self.levels:
            if count >= level.get("count", 0):
                matched_level = level

        return matched_level

    @property
    def current_count(self) -> int:
        now = time.time()
        cutoff = now - self.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()
        return len(self._timestamps)


class SlapEngine:
    """Main slap detection engine.

    Loads slap config, selects the best detection method,
    and dispatches actions based on slap strength or escalation.
    """

    def __init__(self, config: dict):
        self.config = config
        self.slap_config = config.get("slap", {})
        self.enabled = self.slap_config.get("enabled", False)

        # Slap-to-action mappings
        self.mappings = self.slap_config.get("mappings", {})

        # Escalation mode
        esc_config = self.slap_config.get("escalation", {})
        self.escalation_enabled = esc_config.get("enabled", False)
        self.escalation = None
        if self.escalation_enabled:
            self.escalation = EscalationTracker(
                window_minutes=esc_config.get("window_minutes", 5),
                levels=esc_config.get("levels", []),
            )

        # Stats
        self.stats = {
            "total_slaps": 0,
            "by_strength": {"light": 0, "medium": 0, "hard": 0, "brutal": 0},
        }

    def on_slap(self, slap_info: dict):
        """Callback when a slap is detected by the sensor.

        Args:
            slap_info: Dict from the detector with amplitude, strength, etc.
        """
        strength = slap_info.get("strength", "medium")
        amplitude = slap_info.get("amplitude", 0)

        self.stats["total_slaps"] += 1
        if strength in self.stats["by_strength"]:
            self.stats["by_strength"][strength] += 1

        source = slap_info.get("source", "accelerometer")
        print(f"  👋 SLAP detected! [{strength}] amplitude={amplitude:.3f} via {source}")

        # Determine which action to execute
        action = None

        if self.escalation_enabled and self.escalation:
            # Escalation mode — action depends on cumulative slap count
            level = self.escalation.record_slap()
            if level:
                action = {
                    "action": level.get("action", "notify"),
                    "value": str(level.get("value", "")),
                    "label": level.get("label", f"Escalation Level"),
                }
                count = self.escalation.current_count
                print(f"  📈 Escalation: {count} slaps in window → {action['label']}")
        else:
            # Strength-based mapping — look for specific strength, fall back to "any"
            mapping = self.mappings.get(strength) or self.mappings.get("any")
            if mapping:
                action = {
                    "action": mapping.get("action", "notify"),
                    "value": str(mapping.get("value", "")),
                    "label": mapping.get("label", f"Slap {strength}"),
                }

        if action:
            context = {
                "zone": "slap",
                "gesture": strength,
                "tap_count": 1,
                "fingers": 0,
                "x": 0.5,
                "y": 0.5,
                "timestamp": slap_info.get("timestamp", time.time()),
                "slap_info": slap_info,
            }
            try:
                execute_action(action, context)
            except Exception as e:
                print(f"  ❌ Slap action error: {e}")
        else:
            print(f"  ℹ️  No action mapped for slap strength: {strength}")

    def start(self):
        """Start slap detection in a background thread."""
        if not self.enabled:
            return None

        method = self.slap_config.get("method", "auto")
        accel_config = self.slap_config.get("accelerometer", {})
        mic_config = self.slap_config.get("microphone", {})
        cooldown = self.slap_config.get("cooldown_ms", 750)

        thread = threading.Thread(
            target=self._run_detector,
            args=(method, accel_config, mic_config, cooldown),
            daemon=True,
        )
        thread.start()
        return thread

    def _run_detector(self, method: str, accel_config: dict, mic_config: dict, cooldown: int):
        """Run the appropriate detector."""
        if method == "auto":
            method = self._detect_best_method()

        print(f"\n  🔍 Slap detection method: {method}")

        if method == "accelerometer":
            self._run_accelerometer(accel_config, cooldown)
        elif method == "microphone":
            self._run_microphone(mic_config, cooldown)
        else:
            print(f"  ❌ Unknown slap detection method: {method}")

    def _detect_best_method(self) -> str:
        """Auto-detect the best available slap detection method."""
        import os

        if sys.platform == "darwin":
            # Check if we're on Apple Silicon with root
            import platform
            is_arm = platform.machine() == "arm64"
            is_root = os.geteuid() == 0

            if is_arm and is_root:
                print("  ✅ Apple Silicon detected + root access → using accelerometer")
                return "accelerometer"
            elif is_arm and not is_root:
                print("  ⚠️  Apple Silicon detected but no root access")
                print("     For accelerometer: run with sudo")
                print("     Falling back to microphone detection")
                return "microphone"

        # Default fallback
        print("  ℹ️  Using microphone-based detection (cross-platform)")
        return "microphone"

    def _run_accelerometer(self, config: dict, cooldown: int):
        """Start accelerometer-based detection."""
        try:
            from tapcraft.platforms.accel_macos import start_accelerometer_listener
            start_accelerometer_listener(
                on_slap=self.on_slap,
                min_amplitude=config.get("min_amplitude", 0.15),
                cooldown_ms=cooldown,
            )
        except ImportError as e:
            print(f"  ⚠️  Accelerometer unavailable: {e}")
            print("  Falling back to microphone detection...")
            mic_config = self.slap_config.get("microphone", {})
            self._run_microphone(mic_config, cooldown)

    def _run_microphone(self, config: dict, cooldown: int):
        """Start microphone-based detection."""
        try:
            from tapcraft.platforms.mic_slap import start_mic_listener
            start_mic_listener(
                on_slap=self.on_slap,
                threshold=config.get("threshold", 0.3),
                cooldown_ms=cooldown,
            )
        except ImportError as e:
            print(f"  ❌ Microphone detection unavailable: {e}")
            print("     Install: pip install sounddevice numpy")

    def print_stats(self):
        """Print slap statistics."""
        print(f"\n  👋 Slap Stats:")
        print(f"     Total: {self.stats['total_slaps']}")
        for strength, count in self.stats["by_strength"].items():
            if count > 0:
                print(f"     {strength}: {count}")
        if self.escalation:
            print(f"     Current escalation count: {self.escalation.current_count}")
