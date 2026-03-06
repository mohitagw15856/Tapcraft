# Plugins Directory

Custom TapCraft action plugins live here. Each plugin is a Python file
containing a class that inherits from `TapPlugin`.

## Quick Start

```python
# plugins/my_action.py
from tapcraft.plugin import TapPlugin

class MyAction(TapPlugin):
    name = "my-action"  # This is the action type in config.yaml

    def execute(self, value: str, context: dict):
        print(f"Triggered in zone: {context['zone']}")
```

Then in `config.yaml`:

```yaml
  center:
    double:
      action: my-action
      value: "hello"
      label: "My Custom Action"
```

## Context dict

Your `execute()` method receives a `context` dict with:

| Key | Type | Description |
|-----|------|-------------|
| `zone` | str | Which trackpad zone (or "slap") |
| `gesture` | str | Gesture type or slap strength |
| `tap_count` | int | Number of taps |
| `fingers` | int | Number of fingers (0 for slaps) |
| `x` | float | Normalized X position (0-1) |
| `y` | float | Normalized Y position (0-1) |
| `timestamp` | float | Unix timestamp |
| `slap_info` | dict | (slap only) Amplitude, strength, etc. |

## Plugin Ideas

- Spotify / Apple Music integration
- Smart home controls (Hue lights, Home Assistant)
- Pomodoro timer
- Screenshot tool
- Window tiling manager
- Quick emoji picker
- Text expansion / snippets
- Git status notifier
