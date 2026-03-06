"""Shared utility functions for TapCraft."""

import sys


def get_platform() -> str:
    """Return the current platform: 'macos', 'windows', or 'linux'."""
    if sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    else:
        return "linux"


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp a value to the given range."""
    return max(low, min(high, value))


BANNER = r"""
  _____           ____            __ _
 |_   _|_ _ _ __ / ___|_ __ __ _ / _| |_
   | |/ _` | '_ \| |   | '__/ _` | |_| __|
   | | (_| | |_) | |___| | | (_| |  _| |_
   |_|\__,_| .__/ \____|_|  \__,_|_|  \__|
            |_|
"""


def print_banner():
    """Print the TapCraft ASCII banner."""
    print(BANNER)
    print(f"  v0.1.0 — Running on {get_platform()}\n")
