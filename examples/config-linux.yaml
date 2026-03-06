# Platform Setup Guide

TapCraft works on macOS, Windows, and Linux but each platform has different capabilities and setup steps. This guide tells you exactly what to do.

---

## macOS (Best Experience)

**Setup:**

    git clone https://github.com/YOUR_USERNAME/tapcraft.git
    cd tapcraft
    pip install pyyaml pyobjc-framework-Quartz pyobjc-framework-Cocoa

**Use the macOS config:**

    cp examples/config-macos.yaml config.yaml

**Run:**

    python tapcraft.py              # trackpad only
    sudo python tapcraft.py         # trackpad + accelerometer slap detection

**How it works:** Direct multi-touch trackpad access. Tapping different physical areas of your trackpad triggers different zones. Two-finger and three-finger taps are detected natively.

**Slap detection:** On Apple Silicon (M2+), the accelerometer detects physical hits. Requires sudo. On Intel Macs, falls back to microphone (install sounddevice + numpy).

**Grant permissions:** When prompted, allow TapCraft in System Preferences → Privacy & Security → Accessibility.

---

## Windows

**Setup:**

    git clone https://github.com/YOUR_USERNAME/tapcraft.git
    cd tapcraft
    pip install pyyaml pynput

**Use the Windows config:**

    copy examples\config-windows.yaml config.yaml

**Run:**

    python tapcraft.py --log

**How it works:** Two input methods run simultaneously:

1. **Screen grid** — Your screen is divided into a 3x3 grid. Clicking in the top-left area of your screen triggers the top-left zone, clicking in the center triggers center, etc. Double-click for double-tap actions.

2. **Keyboard hotkeys** — Press Ctrl+Alt+Numpad to trigger zones directly:

        7=top-left    8=top-mid    9=top-right
        4=mid-left    5=center     6=mid-right
        1=bot-left    2=bot-mid    3=bot-right

Right-click counts as a two-finger tap. Middle-click counts as three-finger.

**Slap detection (optional):** Uses the microphone. Install extra dependencies first:

    pip install sounddevice numpy --only-binary=:all:
    python tapcraft.py --slap-only --slap-method mic

**Run as Administrator** for best global input capture.

---

## Linux

**Setup:**

    git clone https://github.com/YOUR_USERNAME/tapcraft.git
    cd tapcraft
    pip install pyyaml evdev pynput

    # Add yourself to the input group (required for trackpad access)
    sudo usermod -aG input $USER
    # Then log out and back in

**Use the Linux config:**

    cp examples/config-linux.yaml config.yaml

**Run:**

    python tapcraft.py --log

**How it works:** Reads raw trackpad events via the evdev interface. Multi-touch detection depends on your trackpad hardware and driver (most modern laptops work).

**Slap detection (optional):**

    pip install sounddevice numpy
    python tapcraft.py --slap-only --slap-method mic

---

## Cross-Platform Config Notes

The default `config.yaml` uses only `notify` actions so it works everywhere without changes. To add platform-specific commands, use the `command` action:

**macOS commands:**

    action: command
    value: "open -a 'Terminal'"

    action: command
    value: "say 'Hello from TapCraft'"

**Windows commands:**

    action: command
    value: "start cmd"

    action: command
    value: "start notepad"

    action: command
    value: "start taskmgr"

**Linux commands:**

    action: command
    value: "gnome-terminal"

    action: command
    value: "xdg-open https://google.com"

The `open-app` action is cross-platform and handles the differences automatically:

    action: open-app
    value: "Terminal"       # works on macOS
    value: "notepad"        # works on Windows
    value: "firefox"        # works on Linux

The `notify`, `media`, `clipboard`, `type-text`, and `sound` actions all work on every platform.
