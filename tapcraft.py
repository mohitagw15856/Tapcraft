#!/usr/bin/env python3
"""TapCraft — Turn your trackpad into a programmable command surface.

Usage:
    python tapcraft.py                  # Start TapCraft (trackpad + slap)
    python tapcraft.py --slap-only      # Slap detection only (no trackpad)
    python tapcraft.py --trackpad-only  # Trackpad only (no slap detection)
    python tapcraft.py --configure      # Interactive configuration
    python tapcraft.py --config FILE    # Use a specific config file
    python tapcraft.py --log            # Start with tap logging enabled
    python tapcraft.py --dry-run        # Show config and exit
    python tapcraft.py --test-actions   # Test all configured actions

Slap detection:
    sudo python tapcraft.py --slap-only                   # Accelerometer (macOS Apple Silicon)
    python tapcraft.py --slap-only --slap-method mic      # Microphone (any platform)
    python tapcraft.py --slap-only --slap-sensitivity 0.1 # More sensitive
    python tapcraft.py --escalation                       # Escalation mode (more slaps = crazier)
"""

import argparse
import signal
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tapcraft.config import load_config, print_config_summary
from tapcraft.actions import execute_action
from tapcraft.core import TapCraftEngine
from tapcraft.utils import print_banner, get_platform


def main():
    parser = argparse.ArgumentParser(
        description="TapCraft — programmable trackpad actions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="Path to config.yaml file",
    )
    parser.add_argument(
        "--configure",
        action="store_true",
        help="Launch interactive configurator",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Enable tap logging (overrides config)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load config, show summary, and exit",
    )
    parser.add_argument(
        "--test-actions",
        action="store_true",
        help="Test all configured actions one by one",
    )
    parser.add_argument(
        "--slap-only",
        action="store_true",
        help="Run slap detection only (no trackpad listener)",
    )
    parser.add_argument(
        "--trackpad-only",
        action="store_true",
        help="Run trackpad listener only (no slap detection)",
    )
    parser.add_argument(
        "--slap-method",
        type=str,
        choices=["auto", "accelerometer", "mic"],
        default=None,
        help="Force slap detection method (overrides config)",
    )
    parser.add_argument(
        "--slap-sensitivity",
        type=float,
        default=None,
        help="Slap sensitivity: lower = more sensitive (accelerometer: 0.05-0.5, mic: 0.1-0.8)",
    )
    parser.add_argument(
        "--escalation",
        action="store_true",
        help="Enable escalation mode (more slaps = crazier responses)",
    )

    args = parser.parse_args()

    # Banner
    print_banner()

    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        sys.exit(1)

    # Override log setting if --log flag used
    if args.log:
        config["settings"]["log_taps"] = True

    # Show config summary
    print_config_summary(config)

    # Dry run — just show config and exit
    if args.dry_run:
        print("✅ Config looks good! (dry run — exiting)")
        sys.exit(0)

    # Interactive configurator
    if args.configure:
        run_configurator(config)
        sys.exit(0)

    # Test actions
    if args.test_actions:
        run_action_tests(config)
        sys.exit(0)

    # Start the engine
    engine = TapCraftEngine(config=config, action_handler=execute_action)

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        engine.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    engine.start()

    # --- Start Slap Detection ---
    slap_engine = None
    slap_enabled = config.get("slap", {}).get("enabled", False)

    if not args.trackpad_only and slap_enabled:
        from tapcraft.slap import SlapEngine

        # Apply CLI overrides to slap config
        if args.slap_method:
            method = "microphone" if args.slap_method == "mic" else args.slap_method
            config["slap"]["method"] = method

        if args.slap_sensitivity is not None:
            config["slap"]["accelerometer"]["min_amplitude"] = args.slap_sensitivity
            config["slap"]["microphone"]["threshold"] = args.slap_sensitivity

        if args.escalation:
            config["slap"]["escalation"]["enabled"] = True

        slap_engine = SlapEngine(config)

        # Print slap config summary
        slap_cfg = config["slap"]
        print("\n  👋 Slap Detection: ENABLED")
        print(f"     Method: {slap_cfg.get('method', 'auto')}")
        if slap_engine.escalation_enabled:
            print(f"     Escalation mode: ON")
        slap_mappings = slap_cfg.get("mappings", {})
        for strength, mapping in slap_mappings.items():
            label = mapping.get("label", mapping.get("action", ""))
            print(f"     {strength:>8} → {label}")

        slap_thread = slap_engine.start()
        print()
    elif args.trackpad_only:
        print("\n  👋 Slap Detection: DISABLED (--trackpad-only)")
    elif not slap_enabled:
        print("\n  👋 Slap Detection: DISABLED (set slap.enabled: true in config)")

    # --- Slap-only mode: just wait ---
    if args.slap_only:
        if not slap_enabled:
            print("❌ Slap detection is disabled in config.")
            print("   Set 'slap.enabled: true' in config.yaml")
            sys.exit(1)
        print("  Running in slap-only mode (no trackpad listener).")
        print("  Press Ctrl+C to stop.\n")
        try:
            while True:
                import time as _time
                _time.sleep(1)
        except KeyboardInterrupt:
            engine.stop()
            if slap_engine:
                slap_engine.print_stats()
            sys.exit(0)

    # --- Start platform-specific trackpad listener ---
    platform = get_platform()
    print(f"  Platform: {platform}\n")

    try:
        if platform == "macos":
            from tapcraft.platforms.macos import start_listener
        elif platform == "windows":
            from tapcraft.platforms.windows import start_listener
        elif platform == "linux":
            from tapcraft.platforms.linux import start_listener
        else:
            print(f"❌ Unsupported platform: {platform}")
            sys.exit(1)

        start_listener(engine)

    except KeyboardInterrupt:
        engine.stop()
    except ImportError as e:
        print(f"\n❌ Missing platform dependencies: {e}")
        print(f"\n   Install them with:")
        if platform == "macos":
            print("   pip install pyobjc-framework-Quartz pyobjc-framework-Cocoa rumps")
        elif platform == "windows":
            print("   pip install pynput")
        elif platform == "linux":
            print("   pip install evdev pynput")
        sys.exit(1)


def run_configurator(config: dict):
    """Simple interactive configurator."""
    from tapcraft.config import VALID_ZONES, VALID_GESTURES, VALID_ACTIONS
    import yaml

    print("\n🔧 TapCraft Interactive Configurator")
    print("=" * 50)
    print("\nThis will help you set up tap mappings.")
    print("Press Ctrl+C at any time to save and exit.\n")

    mappings = config.get("mappings", {})

    try:
        while True:
            print("\nAvailable zones:")
            for i, zone in enumerate(VALID_ZONES):
                marker = " ✓" if zone in mappings else ""
                print(f"  {i + 1}. {zone}{marker}")

            choice = input("\nSelect zone number (or 'q' to save & quit): ").strip()
            if choice.lower() == "q":
                break
            try:
                zone = VALID_ZONES[int(choice) - 1]
            except (ValueError, IndexError):
                print("  Invalid choice, try again.")
                continue

            print(f"\nGestures for '{zone}':")
            for i, gesture in enumerate(VALID_GESTURES):
                current = mappings.get(zone, {}).get(gesture)
                marker = f" → {current['label']}" if current else ""
                print(f"  {i + 1}. {gesture}{marker}")

            choice = input("Select gesture number: ").strip()
            try:
                gesture = VALID_GESTURES[int(choice) - 1]
            except (ValueError, IndexError):
                print("  Invalid choice.")
                continue

            print(f"\nAction types:")
            for i, action in enumerate(VALID_ACTIONS):
                print(f"  {i + 1}. {action}")

            choice = input("Select action number: ").strip()
            try:
                action_type = VALID_ACTIONS[int(choice) - 1]
            except (ValueError, IndexError):
                print("  Invalid choice.")
                continue

            value = input(f"Value for '{action_type}': ").strip()
            label = input("Label (optional, press Enter to skip): ").strip()
            if not label:
                label = f"{zone} {gesture}"

            if zone not in mappings:
                mappings[zone] = {}

            mappings[zone][gesture] = {
                "action": action_type,
                "value": value,
                "label": label,
            }

            print(f"\n  ✅ Added: {zone}/{gesture} → {action_type}: {value}")

    except (KeyboardInterrupt, EOFError):
        pass

    # Save
    config["mappings"] = mappings
    config_path = os.path.join(os.getcwd(), "config.yaml")

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"\n\n💾 Config saved to: {config_path}")
    print("   Run 'python tapcraft.py' to start!\n")


def run_action_tests(config: dict):
    """Test all configured actions."""
    import time

    mappings = config.get("mappings", {})
    if not mappings:
        print("  No mappings to test!")
        return

    print("\n🧪 Testing all configured actions...")
    print("=" * 50)

    for zone, gestures in mappings.items():
        for gesture, action in gestures.items():
            label = action.get("label", action["action"])
            print(f"\n  Testing: {label} ({zone}/{gesture})")
            print(f"  Action:  {action['action']} → {action['value']}")

            context = {
                "zone": zone,
                "gesture": gesture,
                "tap_count": 1,
                "fingers": 1,
                "x": 0.5,
                "y": 0.5,
                "timestamp": time.time(),
            }

            try:
                execute_action(action, context)
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"  ❌ Error: {e}")

    print("\n✅ Action tests complete!\n")


if __name__ == "__main__":
    main()
