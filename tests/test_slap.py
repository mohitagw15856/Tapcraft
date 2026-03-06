"""Tests for TapCraft slap detection engine."""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tapcraft.slap import SlapEngine, EscalationTracker


class TestEscalationTracker(unittest.TestCase):

    def test_no_levels(self):
        tracker = EscalationTracker(window_minutes=1, levels=[])
        result = tracker.record_slap()
        self.assertIsNone(result)

    def test_first_level(self):
        levels = [
            {"count": 1, "action": "notify", "value": "Level 1", "label": "L1"},
            {"count": 5, "action": "notify", "value": "Level 2", "label": "L2"},
        ]
        tracker = EscalationTracker(window_minutes=5, levels=levels)

        result = tracker.record_slap()
        self.assertIsNotNone(result)
        self.assertEqual(result["label"], "L1")

    def test_escalation_to_level_2(self):
        levels = [
            {"count": 1, "action": "notify", "value": "Level 1", "label": "L1"},
            {"count": 3, "action": "notify", "value": "Level 2", "label": "L2"},
        ]
        tracker = EscalationTracker(window_minutes=5, levels=levels)

        # 3 slaps should reach level 2
        for _ in range(3):
            result = tracker.record_slap()

        self.assertEqual(result["label"], "L2")

    def test_count_tracking(self):
        tracker = EscalationTracker(window_minutes=5, levels=[])
        tracker.record_slap()
        tracker.record_slap()
        tracker.record_slap()
        self.assertEqual(tracker.current_count, 3)

    def test_window_expiry(self):
        # Use a very short window
        tracker = EscalationTracker(window_minutes=0.001, levels=[])  # ~0.06 seconds
        tracker.record_slap()
        time.sleep(0.1)
        # After window expires, count should reset
        self.assertEqual(tracker.current_count, 0)


class TestSlapEngine(unittest.TestCase):

    def _make_config(self, enabled=True, escalation=False):
        return {
            "settings": {},
            "mappings": {},
            "slap": {
                "enabled": enabled,
                "method": "auto",
                "accelerometer": {"min_amplitude": 0.15},
                "microphone": {"threshold": 0.3, "spike_ratio": 4.0},
                "cooldown_ms": 750,
                "mappings": {
                    "any": {"action": "notify", "value": "Slap!", "label": "Any Slap"},
                    "light": {"action": "notify", "value": "Light!", "label": "Light"},
                    "hard": {"action": "notify", "value": "Hard!", "label": "Hard"},
                },
                "escalation": {
                    "enabled": escalation,
                    "window_minutes": 5,
                    "levels": [
                        {"count": 1, "action": "notify", "value": "L1", "label": "Level 1"},
                    ],
                },
            },
        }

    def test_engine_creation(self):
        config = self._make_config()
        engine = SlapEngine(config)
        self.assertTrue(engine.enabled)
        self.assertFalse(engine.escalation_enabled)

    def test_engine_disabled(self):
        config = self._make_config(enabled=False)
        engine = SlapEngine(config)
        self.assertFalse(engine.enabled)

    def test_strength_mapping(self):
        config = self._make_config()
        engine = SlapEngine(config)

        # Check that mappings are loaded
        self.assertIn("any", engine.mappings)
        self.assertIn("light", engine.mappings)
        self.assertIn("hard", engine.mappings)

    def test_escalation_mode(self):
        config = self._make_config(escalation=True)
        engine = SlapEngine(config)
        self.assertTrue(engine.escalation_enabled)
        self.assertIsNotNone(engine.escalation)

    def test_stats_tracking(self):
        config = self._make_config()
        engine = SlapEngine(config)

        # Simulate a slap (we can't test actual action execution easily)
        self.assertEqual(engine.stats["total_slaps"], 0)


class TestAccelSample(unittest.TestCase):
    """Test the accelerometer sample class."""

    def test_import(self):
        # Only test the sample class, not IOKit bindings
        # accel_macos.py will fail to import on non-macOS
        if sys.platform != "darwin":
            self.skipTest("macOS only")

    def test_magnitude_at_rest(self):
        """At rest, total magnitude should be ~1g, so dynamic magnitude ~0."""
        if sys.platform != "darwin":
            self.skipTest("macOS only")
        # Simulate resting with ~1g on z-axis
        from tapcraft.platforms.accel_macos import AccelSample
        sample = AccelSample(x=0.0, y=0.0, z=1.0, t=time.time())
        self.assertAlmostEqual(sample.magnitude, 0.0, places=2)

    def test_magnitude_with_impact(self):
        """During impact, magnitude should be significantly > 0."""
        if sys.platform != "darwin":
            self.skipTest("macOS only")
        from tapcraft.platforms.accel_macos import AccelSample
        sample = AccelSample(x=0.5, y=0.3, z=1.2, t=time.time())
        self.assertGreater(sample.magnitude, 0.1)


if __name__ == "__main__":
    unittest.main()
