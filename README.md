# 🎯 TapCraft

**Turn your trackpad into a programmable command surface.**

TapCraft lets you assign custom actions to different tap zones, tap patterns, and multi-finger gestures on your trackpad. Make your laptop *yours* — trigger sounds, shortcuts, scripts, or anything you can imagine, just by tapping.

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## ✨ What Can You Do?

| Tap Pattern | Example Action |
|---|---|
| Double-tap top-left corner | Toggle Do Not Disturb |
| Triple-tap center | Play a fun sound effect |
| Two-finger tap right edge | Paste from clipboard history |
| Three-finger tap bottom-left | Open terminal |
| Tap pattern: 2-1-2 | Secret macro / easter egg |

**Actions include:** play sounds, run shell commands, type text, open apps, send notifications, control media, manage clipboard, and more. Or write your own action plugin!

---

## 🚀 Quick Start

### 1. Install

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/tapcraft.git
cd tapcraft

# Install dependencies
pip install -r requirements.txt

# macOS only — grant Accessibility permissions when prompted
```

### 2. Run

```bash
python tapcraft.py
```

That's it! TapCraft starts with a sensible default config. A system tray icon appears so you can pause/resume/configure anytime.

### 3. Configure

Edit `config.yaml` (auto-created on first run), or use the built-in configurator:

```bash
python tapcraft.py --configure
```

---

## 🗺️ Trackpad Zones

TapCraft divides your trackpad into a 3×3 grid:

```
┌──────────┬──────────┬──────────┐
│ top-left │ top-mid  │ top-right│
├──────────┼──────────┼──────────┤
│ mid-left │  center  │mid-right │
├──────────┼──────────┼──────────┤
│ bot-left │ bot-mid  │bot-right │
└──────────┴──────────┴──────────┘
```

Each zone can have different actions for:
- **Single tap** (1 finger)
- **Double tap** (1 finger, quick succession)
- **Triple tap** (1 finger, quick succession)
- **Two-finger tap**
- **Three-finger tap**

---

## ⚙️ Configuration

The `config.yaml` file is the heart of TapCraft. Here's a sample:

```yaml
# TapCraft Configuration
# Zones: top-left, top-mid, top-right, mid-left, center, mid-right, bot-left, bot-mid, bot-right
# Gestures: single, double, triple, two-finger, three-finger
# Actions: sound, command, notify, type-text, open-app, media, clipboard

settings:
  tap_timeout_ms: 300        # Max time between taps for multi-tap detection
  zone_padding: 0.05         # Dead zone between regions (0-0.15)
  feedback: true             # Visual/audio feedback on trigger
  log_taps: false            # Log all taps (useful for debugging)

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
      value: "TapCraft is alive! 🎉"
      label: "Test Notification"

  bot-left:
    two-finger:
      action: type-text
      value: "¯\\_(ツ)_/¯"
      label: "Shrug Emoji"

  bot-right:
    single:
      action: clipboard
      value: "paste-plain"
      label: "Paste as Plain Text"
```

### Action Types

| Action | Description | Value Format |
|---|---|---|
| `sound` | Play a WAV/MP3 file | Path to sound file |
| `command` | Run a shell command | Any shell command |
| `notify` | Show a system notification | Notification text |
| `type-text` | Type text at cursor | Text to type |
| `open-app` | Launch an application | App name or path |
| `media` | Media control | `play-pause`, `next`, `prev`, `vol-up`, `vol-down` |
| `clipboard` | Clipboard operations | `paste-plain`, `copy-line`, `clipboard-history` |
| `script` | Run a Python script | Path to .py file |

---

## 👋 Slap Detection (inspired by [taigrr/spank](https://github.com/taigrr/spank))

TapCraft can detect physical slaps and hits on your laptop body — and trigger configurable actions based on how hard you hit it!

### How It Works

**macOS Apple Silicon (M2+):** Reads the built-in MEMS accelerometer (Bosch BMI286 IMU) via IOKit HID. This detects actual physical impacts with high precision. Requires `sudo`.

**Windows / Linux / Intel Macs:** Falls back to microphone-based detection — the mic picks up the sharp percussive sound of a slap surprisingly well. No special permissions needed.

### Quick Start — Slap Mode

```bash
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
```

### Strength-Based Actions

TapCraft classifies each hit by strength and lets you assign different actions:

```yaml
slap:
  enabled: true
  method: auto          # auto, accelerometer, or microphone

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
    any:                # fallback for any strength
      action: sound
      value: "sounds/pop.wav"
```

### Escalation Mode

Inspired by spank's `--sexy` mode. The more you slap within a time window, the more intense the response:

```yaml
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
```

---

## 🔊 Bundled Sounds

TapCraft includes a few fun sounds in the `sounds/` directory:

- `ping.wav` — Clean notification ping
- `click.wav` — Satisfying mechanical click
- `whoosh.wav` — Transition swoosh
- `pop.wav` — Bubble pop

Drop your own `.wav` or `.mp3` files in `sounds/` and reference them in your config!

---

## 🧩 Writing Custom Action Plugins

Create a Python file in the `plugins/` directory:

```python
# plugins/my_action.py
from tapcraft.plugin import TapPlugin

class MyAction(TapPlugin):
    """A custom action that does something cool."""
    name = "my-action"

    def execute(self, value: str, context: dict):
        # value = whatever is in the config "value" field
        # context = {zone, gesture, tap_count, fingers, x, y, timestamp}
        print(f"Custom action triggered in {context['zone']}!")
```

Then use it in config:

```yaml
  center:
    double:
      action: my-action
      value: "hello"
      label: "My Custom Action"
```

---

## 🖥️ Platform Notes

### macOS (Best Experience)
- Full multi-touch trackpad support via Quartz Event Taps
- Requires **Accessibility permissions** (System Preferences → Privacy & Security → Accessibility)
- Supports all zones and gesture types

### Windows
- Uses raw trackpad input via ctypes/WinAPI
- Most trackpad features work; multi-touch depends on driver support (Precision Touchpads work best)
- Run as Administrator for global input capture

### Linux
- Uses `/dev/input/` evdev interface for trackpad events
- Requires `libinput` and user must be in the `input` group
- Run: `sudo usermod -aG input $USER` then log out/in

---

## 📁 Project Structure

```
tapcraft/
├── tapcraft.py              # Main entry point
├── config.yaml              # User configuration (auto-created)
├── requirements.txt         # Python dependencies
├── tapcraft/
│   ├── __init__.py
│   ├── core.py              # Core engine: zone detection, gesture recognition
│   ├── config.py            # Config loader/validator
│   ├── actions.py           # Built-in action handlers
│   ├── slap.py              # Slap detection engine + escalation mode
│   ├── plugin.py            # Plugin base class
│   ├── sounds.py            # Sound playback engine
│   ├── tray.py              # System tray UI
│   ├── platforms/
│   │   ├── __init__.py
│   │   ├── macos.py         # macOS trackpad listener
│   │   ├── windows.py       # Windows trackpad listener
│   │   ├── linux.py         # Linux evdev listener
│   │   ├── accel_macos.py   # macOS accelerometer (IOKit HID)
│   │   └── mic_slap.py      # Microphone-based slap detection
│   └── utils.py             # Shared utilities
├── plugins/                 # Community / user plugins
│   └── example_plugin.py
├── sounds/                  # Sound files
│   └── ...
├── tests/
│   ├── test_core.py
│   ├── test_config.py
│   └── test_slap.py
├── LICENSE
├── CONTRIBUTING.md
└── .github/
    └── ISSUE_TEMPLATE/
        ├── bug_report.md
        └── feature_request.md
```

---

## 🤝 Contributing

We'd love your contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ideas for contributions:**
- 🎵 New sound packs
- 🧩 Action plugins (Spotify control, smart home, etc.)
- 🖥️ Better Windows/Linux trackpad support
- 🎨 GUI configurator
- 📱 Gesture visualizer overlay
- 🔗 Integration with Alfred, Raycast, AutoHotkey

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

**Made with ❤️ by the TapCraft community. Star ⭐ this repo if you find it useful!**
