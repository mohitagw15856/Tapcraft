# TapCraft

**Turn your trackpad into a programmable command surface.**

<img width="768" height="512" alt="ChatGPT Image Mar 6, 2026, 07_32_15 PM" src="https://github.com/user-attachments/assets/1f07fe44-5fce-4dd3-964b-2cbfae71ab25" />


TapCraft lets you assign custom actions to different tap zones, tap patterns, and multi-finger gestures on your trackpad. It also detects physical slaps on your laptop body (inspired by [taigrr/spank](https://github.com/taigrr/spank)) and maps them to actions based on hit strength.

Make your laptop *yours* — trigger sounds, shortcuts, scripts, or anything you can imagine.

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## What Can You Do?

| Tap Pattern | Example Action |
|---|---|
| Double-tap top-left corner | Open Terminal |
| Triple-tap center | Play a fun sound effect |
| Two-finger tap right edge | Paste from clipboard history |
| Three-finger tap bottom-left | Open an app |
| Slap the laptop (light) | Show a notification |
| Slap the laptop (hard) | Run a shell command |
| Slap it 20 times in 5 min | Your Mac says "please stop hitting me!" |

**Actions include:** play sounds, run shell commands, type text, open apps, send notifications, control media, manage clipboard, run Python scripts, and community plugins.

---

## Quick Start

**1. Install**

    git clone https://github.com/mohitagw15856/Tapcraft.git
    cd tapcraft
    pip install -r requirements.txt

**2. Launch the GUI**

    python tapcraft_gui.py

This opens a visual configurator where you can click zones, pick actions from dropdowns, toggle slap detection, and start/stop TapCraft — all without touching the terminal or editing YAML files.

**Or run from the command line:**

    python tapcraft.py --log

**3. Platform-specific setup?** See [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md) for macOS, Windows, and Linux details.

---

## GUI Configurator

TapCraft ships with a built-in visual configurator. No YAML editing required.

    python tapcraft_gui.py

**Trackpad Zones tab** — Click any zone in the 3x3 grid to configure its actions. Pick action types from dropdowns, set values, and save.

**Slap Detection tab** — Toggle slap detection on/off, adjust sensitivity with a slider, set cooldown, configure strength-based actions, and enable escalation mode.

**Settings tab** — Tune tap timeout, zone padding, and toggle debug logging.

**Start/Stop button** — Saves your config and launches TapCraft in one click. Hit it again to stop.

You can also edit `config.yaml` directly if you prefer. The GUI and the YAML file stay in sync.

---

## Trackpad Zones

TapCraft divides your trackpad into a 3x3 grid:

    ┌──────────┬──────────┬──────────┐
    │ top-left │ top-mid  │ top-right│
    ├──────────┼──────────┼──────────┤
    │ mid-left │  center  │mid-right │
    ├──────────┼──────────┼──────────┤
    │ bot-left │ bot-mid  │bot-right │
    └──────────┴──────────┴──────────┘

Each zone supports five gesture types: **single tap**, **double tap**, **triple tap**, **two-finger tap**, and **three-finger tap**. That's 45 possible trigger combinations on a surface you're already touching all day.

---

## Configuration

The `config.yaml` file is the heart of TapCraft. Here's a sample:

    settings:
      tap_timeout_ms: 300
      zone_padding: 0.05
      feedback: true
      log_taps: false

    mappings:
      top-left:
        double:
          action: command
          value: "open -a 'Terminal'"
          label: "Open Terminal"

      top-right:
        double:
          action: sound
          value: "sounds/ping.wav"
          label: "Ping!"

      center:
        triple:
          action: notify
          value: "TapCraft is alive!"
          label: "Test Notification"

      bot-left:
        two-finger:
          action: type-text
          value: "shrug_face"
          label: "Shrug Emoji"

      bot-right:
        single:
          action: clipboard
          value: "paste-plain"
          label: "Paste as Plain Text"

### Action Types

| Action | Description | Value Format |
|---|---|---|
| `sound` | Play a WAV/MP3 file | Path to sound file |
| `command` | Run a shell command | Any shell command |
| `notify` | Show a system notification | Notification text |
| `type-text` | Type text at cursor | Text to type |
| `open-app` | Launch an application | App name or path |
| `media` | Media control | play-pause, next, prev, vol-up, vol-down |
| `clipboard` | Clipboard operations | paste-plain, copy-line |
| `script` | Run a Python script | Path to .py file |

---

## Slap Detection

Inspired by [taigrr/spank](https://github.com/taigrr/spank). TapCraft detects physical slaps and hits on your laptop body and triggers configurable actions based on how hard you hit it.

**macOS Apple Silicon (M2+):** Reads the built-in MEMS accelerometer (Bosch BMI286 IMU) via IOKit HID. Detects actual physical impacts with high precision. Requires `sudo`.

**Windows / Linux / Intel Macs:** Falls back to microphone-based detection — the mic picks up the sharp percussive sound of a slap surprisingly well. No special permissions needed.

### Quick Start — Slap Mode

    # macOS Apple Silicon — best experience (uses accelerometer)
    sudo python tapcraft.py --slap-only

    # Any platform — uses microphone
    python tapcraft.py --slap-only --slap-method mic

    # Adjust sensitivity (lower = more sensitive)
    sudo python tapcraft.py --slap-only --slap-sensitivity 0.1

    # Escalation mode — more slaps = crazier responses!
    sudo python tapcraft.py --slap-only --escalation

    # Run both trackpad + slap detection together
    sudo python tapcraft.py

### Strength-Based Actions

TapCraft classifies each hit by strength and lets you assign different actions:

    slap:
      enabled: true
      method: auto

      mappings:
        light:
          action: notify
          value: "Hey, that tickles!"
        medium:
          action: sound
          value: "sounds/click.wav"
        hard:
          action: command
          value: "open -a 'Terminal'"
        brutal:
          action: notify
          value: "OW! That really hurt!"
        any:
          action: sound
          value: "sounds/pop.wav"

### Escalation Mode

Inspired by spank's `--sexy` mode. The more you slap within a time window, the more intense the response:

    slap:
      escalation:
        enabled: true
        window_minutes: 5
        levels:
          - count: 1
            action: sound
            value: "sounds/ping.wav"
          - count: 5
            action: notify
            value: "Getting warmer..."
          - count: 10
            action: notify
            value: "You really can't stop, can you?"
          - count: 20
            action: command
            value: "say 'Please stop hitting me!'"

---

## Bundled Sounds

Drop your own `.wav` or `.mp3` files in the `sounds/` directory and reference them in your config. Check `sounds/README.md` for links to free sound sources like Freesound.org and Mixkit.

---

## Writing Custom Action Plugins

Create a Python file in the `plugins/` directory:

    # plugins/my_action.py
    from tapcraft.plugin import TapPlugin

    class MyAction(TapPlugin):
        name = "my-action"

        def execute(self, value, context):
            print(f"Custom action triggered in {context['zone']}!")

Then use it in config:

    center:
      double:
        action: my-action
        value: "hello"
        label: "My Custom Action"

---

## Platform Notes

**macOS (Best Experience)** — Full multi-touch trackpad support via Quartz Event Taps. Your physical trackpad is divided into a 3x3 zone grid. Requires Accessibility permissions. Accelerometer slap detection on Apple Silicon M2+.

**Windows** — Your screen is divided into a 3x3 grid matching trackpad zones. Click/tap in different screen areas to trigger zone actions. Also supports Ctrl+Alt+Numpad 1-9 hotkeys for direct zone triggers. Right-click = two-finger, middle-click = three-finger. Microphone-based slap detection. Note: true raw trackpad position detection on Windows requires the Precision Touchpad C API — contributions welcome!

**Linux** — Uses /dev/input/ evdev interface for trackpad events. Requires user to be in the input group (`sudo usermod -aG input $USER` then log out/in). Microphone-based slap detection.

For full setup instructions per platform, see [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md). Pre-made configs are in the `examples/` folder.

---

## Project Structure

    tapcraft/
    ├── tapcraft.py              # Main entry point (CLI)
    ├── tapcraft_gui.py          # Visual configurator (GUI)
    ├── config.yaml              # User configuration (auto-created)
    ├── requirements.txt         # Python dependencies
    ├── setup.py                 # pip install support
    ├── PLATFORM_GUIDE.md        # Setup instructions per OS
    ├── examples/                # Pre-made configs per platform
    │   ├── config-macos.yaml
    │   ├── config-windows.yaml
    │   └── config-linux.yaml
    ├── tapcraft/
    │   ├── __init__.py
    │   ├── core.py              # Zone detection, gesture recognition
    │   ├── config.py            # Config loader/validator
    │   ├── actions.py           # 8 built-in action handlers
    │   ├── slap.py              # Slap engine + escalation mode
    │   ├── plugin.py            # Plugin base class
    │   ├── utils.py             # Shared utilities
    │   └── platforms/
    │       ├── macos.py         # macOS trackpad listener
    │       ├── windows.py       # Windows listener (screen grid + hotkeys)
    │       ├── linux.py         # Linux evdev listener
    │       ├── accel_macos.py   # Apple Silicon accelerometer
    │       └── mic_slap.py      # Microphone slap detection
    ├── plugins/                 # Community / user plugins
    │   └── example_plugin.py
    ├── sounds/                  # Sound files
    ├── tests/                   # 30 unit tests
    ├── LICENSE
    ├── CONTRIBUTING.md
    └── CHANGELOG.md

---

## Contributing

We'd love your contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ideas for contributions:** new sound packs, action plugins (Spotify control, smart home, etc.), native Windows Precision Touchpad support, gesture visualizer overlay, integration with Alfred / Raycast / AutoHotkey.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

**Made with love by the TapCraft community. Star this repo if you find it useful!**

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-yellow?logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/mohit15856)
