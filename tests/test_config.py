"""Tests for TapCraft config module."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tapcraft.config import load_config, get_action


SAMPLE_CONFIG = """
settings:
  tap_timeout_ms: 250
  zone_padding: 0.1
  feedback: true
  log_taps: false

mappings:
  center:
    triple:
      action: notify
      value: "Test!"
      label: "Test Notification"
  top-left:
    double:
      action: command
      value: "echo hello"
      label: "Say Hello"
"""


class TestLoadConfig(unittest.TestCase):

    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        )
        self.tmpfile.write(SAMPLE_CONFIG)
        self.tmpfile.close()

    def tearDown(self):
        os.unlink(self.tmpfile.name)

    def test_load_settings(self):
        config = load_config(self.tmpfile.name)
        self.assertEqual(config["settings"]["tap_timeout_ms"], 250)
        self.assertEqual(config["settings"]["zone_padding"], 0.1)
        self.assertTrue(config["settings"]["feedback"])

    def test_load_mappings(self):
        config = load_config(self.tmpfile.name)
        self.assertIn("center", config["mappings"])
        self.assertIn("triple", config["mappings"]["center"])
        self.assertEqual(config["mappings"]["center"]["triple"]["action"], "notify")

    def test_get_action(self):
        config = load_config(self.tmpfile.name)
        action = get_action(config, "center", "triple")
        self.assertIsNotNone(action)
        self.assertEqual(action["action"], "notify")
        self.assertEqual(action["value"], "Test!")

    def test_get_action_missing(self):
        config = load_config(self.tmpfile.name)
        action = get_action(config, "bot-right", "single")
        self.assertIsNone(action)


class TestInvalidConfig(unittest.TestCase):

    def test_unknown_zone_ignored(self):
        content = """
mappings:
  invalid-zone:
    single:
      action: notify
      value: "test"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()
            config = load_config(f.name)
            self.assertNotIn("invalid-zone", config["mappings"])
        os.unlink(f.name)

    def test_unknown_action_ignored(self):
        content = """
mappings:
  center:
    single:
      action: invalid-action
      value: "test"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(content)
            f.flush()
            config = load_config(f.name)
            self.assertEqual(config["mappings"].get("center", {}), {})
        os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
