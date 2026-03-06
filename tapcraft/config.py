"""Configuration loader and validator for TapCraft."""

import os
import shutil
import yaml
from typing import Any

VALID_ZONES = [
    "top-left", "top-mid", "top-right",
    "mid-left", "center", "mid-right",
    "bot-left", "bot-mid", "bot-right",
]

VALID_GESTURES = ["single", "double", "triple", "two-finger", "three-finger"]

VALID_ACTIONS = [
    "sound", "command", "notify", "type-text",
    "open-app", "media", "clipboard", "script",
]

DEFAULT_SETTINGS = {
    "tap_timeout_ms": 300,
    "zone_padding": 0.05,
    "feedback": True,
    "log_taps": False,
}


def get_config_path() -> str:
    """Return the path to config.yaml, creating a default if it doesn't exist."""
    # Check current directory first, then ~/.tapcraft/
    local_path = os.path.join(os.getcwd(), "config.yaml")
    home_path = os.path.join(os.path.expanduser("~"), ".tapcraft", "config.yaml")

    if os.path.exists(local_path):
        return local_path
    if os.path.exists(home_path):
        return home_path

    # Create default config in current directory
    default_src = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    if os.path.exists(default_src):
        shutil.copy2(default_src, local_path)
    else:
        _create_minimal_config(local_path)

    print(f"📝 Created default config at: {local_path}")
    print("   Edit it to customize your tap actions!\n")
    return local_path


def _create_minimal_config(path: str):
    """Write a minimal starter config."""
    minimal = {
        "settings": DEFAULT_SETTINGS.copy(),
        "mappings": {
            "center": {
                "triple": {
                    "action": "notify",
                    "value": "TapCraft is working!",
                    "label": "Test",
                }
            }
        },
    }
    with open(path, "w") as f:
        yaml.dump(minimal, f, default_flow_style=False, sort_keys=False)


def load_config(path: str = None) -> dict:
    """Load and validate the TapCraft configuration."""
    if path is None:
        path = get_config_path()

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"Config file is not a valid YAML mapping: {path}")

    config = {"settings": {}, "mappings": {}, "slap": {}}

    # --- Settings ---
    raw_settings = raw.get("settings", {}) or {}
    for key, default in DEFAULT_SETTINGS.items():
        config["settings"][key] = raw_settings.get(key, default)

    # --- Slap config (pass through as-is, validated by SlapEngine) ---
    raw_slap = raw.get("slap", {}) or {}
    config["slap"] = raw_slap

    # --- Mappings ---
    raw_mappings = raw.get("mappings", {}) or {}
    for zone, gestures in raw_mappings.items():
        if zone not in VALID_ZONES:
            print(f"⚠️  Ignoring unknown zone '{zone}' in config")
            continue
        if not isinstance(gestures, dict):
            continue

        config["mappings"][zone] = {}
        for gesture, action_def in gestures.items():
            if gesture not in VALID_GESTURES:
                print(f"⚠️  Ignoring unknown gesture '{gesture}' in zone '{zone}'")
                continue
            if not isinstance(action_def, dict):
                continue

            action_type = action_def.get("action", "")
            if action_type not in VALID_ACTIONS:
                print(f"⚠️  Ignoring unknown action '{action_type}' in {zone}/{gesture}")
                continue

            config["mappings"][zone][gesture] = {
                "action": action_type,
                "value": str(action_def.get("value", "")),
                "label": action_def.get("label", f"{zone} {gesture}"),
            }

    return config


def get_action(config: dict, zone: str, gesture: str):
    """Look up the action for a given zone + gesture. Returns None if unmapped."""
    return config.get("mappings", {}).get(zone, {}).get(gesture)


def print_config_summary(config: dict):
    """Print a readable summary of the current config."""
    print("\n🎯 TapCraft Configuration")
    print("=" * 50)

    settings = config["settings"]
    print(f"  Tap timeout:  {settings['tap_timeout_ms']}ms")
    print(f"  Zone padding: {settings['zone_padding']}")
    print(f"  Feedback:     {'On' if settings['feedback'] else 'Off'}")
    print(f"  Log taps:     {'On' if settings['log_taps'] else 'Off'}")

    mappings = config["mappings"]
    if not mappings:
        print("\n  No mappings configured! Edit config.yaml to add some.")
        return

    print(f"\n  Mappings ({sum(len(g) for g in mappings.values())} total):")
    print("  " + "-" * 46)
    for zone in VALID_ZONES:
        if zone not in mappings:
            continue
        for gesture, action in mappings[zone].items():
            label = action.get("label", action["action"])
            print(f"  {zone:>10} / {gesture:<13} → {label}")

    print()
