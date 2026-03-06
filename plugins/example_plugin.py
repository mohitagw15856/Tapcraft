"""Example TapCraft plugin — demonstrates how to write custom actions.

To use this plugin:
1. Keep this file in the plugins/ directory
2. Add to your config.yaml:

    center:
      triple:
        action: countdown
        value: "3"
        label: "Countdown Timer"
"""

import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tapcraft.plugin import TapPlugin


class CountdownAction(TapPlugin):
    """A fun countdown timer that prints to console and shows a notification."""

    name = "countdown"

    def execute(self, value: str, context: dict):
        try:
            seconds = int(value)
        except ValueError:
            seconds = 3

        print(f"    ⏱️  Countdown: {seconds}...")
        for i in range(seconds, 0, -1):
            print(f"    {i}...")
            time.sleep(1)
        print("    🎉 Go!")

        # Show notification when done
        from tapcraft.actions import action_notify
        action_notify("⏱️ Countdown complete!", context)


class QuickNoteAction(TapPlugin):
    """Append a timestamped note to a file."""

    name = "quick-note"

    def execute(self, value: str, context: dict):
        """Value should be the note text, or 'prompt' to ask for input."""
        note_file = os.path.expanduser("~/tapcraft_notes.txt")

        if value.lower() == "prompt":
            # In a real app, this could open a GUI dialog
            print("    📝 Quick note feature — would open input dialog")
            return

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{context['zone']}] {value}\n"

        with open(note_file, "a") as f:
            f.write(entry)

        print(f"    📝 Note saved to {note_file}")
