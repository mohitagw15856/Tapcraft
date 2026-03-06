"""Tests for TapCraft core module."""

import sys
import os
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tapcraft.core import detect_zone, TapEvent, GestureRecognizer


class TestZoneDetection(unittest.TestCase):
    """Test the zone detection grid."""

    def test_corners(self):
        self.assertEqual(detect_zone(0.1, 0.1), "top-left")
        self.assertEqual(detect_zone(0.9, 0.1), "top-right")
        self.assertEqual(detect_zone(0.1, 0.9), "bot-left")
        self.assertEqual(detect_zone(0.9, 0.9), "bot-right")

    def test_center(self):
        self.assertEqual(detect_zone(0.5, 0.5), "center")

    def test_edges(self):
        self.assertEqual(detect_zone(0.5, 0.1), "top-mid")
        self.assertEqual(detect_zone(0.5, 0.9), "bot-mid")
        self.assertEqual(detect_zone(0.1, 0.5), "mid-left")
        self.assertEqual(detect_zone(0.9, 0.5), "mid-right")

    def test_dead_zone(self):
        # Exactly on the boundary with padding should be dead zone
        result = detect_zone(1 / 3, 0.5, padding=0.05)
        self.assertEqual(result, "")

    def test_no_padding(self):
        # With zero padding, no dead zones
        result = detect_zone(1 / 3, 0.5, padding=0.0)
        self.assertIn(result, ["mid-left", "center"])


class TestTapEvent(unittest.TestCase):

    def test_creation(self):
        event = TapEvent(x=0.5, y=0.5, fingers=2)
        self.assertEqual(event.x, 0.5)
        self.assertEqual(event.y, 0.5)
        self.assertEqual(event.fingers, 2)
        self.assertIsNotNone(event.timestamp)

    def test_repr(self):
        event = TapEvent(x=0.123, y=0.456, fingers=1)
        self.assertIn("0.12", repr(event))
        self.assertIn("0.46", repr(event))


class TestGestureRecognizer(unittest.TestCase):

    def test_single_tap(self):
        results = []

        def on_gesture(x, y, gesture, taps):
            results.append(gesture)

        recognizer = GestureRecognizer(timeout_ms=100, on_gesture=on_gesture)
        recognizer.feed(TapEvent(x=0.5, y=0.5))

        time.sleep(0.2)  # Wait for timeout
        self.assertEqual(results, ["single"])

    def test_double_tap(self):
        results = []

        def on_gesture(x, y, gesture, taps):
            results.append(gesture)

        recognizer = GestureRecognizer(timeout_ms=200, on_gesture=on_gesture)
        recognizer.feed(TapEvent(x=0.5, y=0.5))
        time.sleep(0.05)
        recognizer.feed(TapEvent(x=0.5, y=0.5))

        time.sleep(0.3)
        self.assertEqual(results, ["double"])

    def test_two_finger_tap(self):
        results = []

        def on_gesture(x, y, gesture, taps):
            results.append(gesture)

        recognizer = GestureRecognizer(timeout_ms=100, on_gesture=on_gesture)
        recognizer.feed(TapEvent(x=0.5, y=0.5, fingers=2))

        time.sleep(0.2)
        self.assertEqual(results, ["two-finger"])

    def test_three_finger_tap(self):
        results = []

        def on_gesture(x, y, gesture, taps):
            results.append(gesture)

        recognizer = GestureRecognizer(timeout_ms=100, on_gesture=on_gesture)
        recognizer.feed(TapEvent(x=0.5, y=0.5, fingers=3))

        time.sleep(0.2)
        self.assertEqual(results, ["three-finger"])


if __name__ == "__main__":
    unittest.main()
