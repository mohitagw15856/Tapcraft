"""Built-in action handlers for TapCraft."""

import os
import sys
import subprocess
import threading


def execute_action(action: dict, context: dict):
    """Dispatch an action to the appropriate handler.

    Args:
        action: Dict with 'action', 'value', and 'label' keys.
        context: Dict with zone, gesture, tap_count, fingers, x, y, timestamp.
    """
    action_type = action["action"]
    value = action["value"]

    handler = ACTION_REGISTRY.get(action_type)
    if handler is None:
        # Try loading as a plugin
        handler = _try_load_plugin(action_type)

    if handler is None:
        print(f"  ⚠️  Unknown action type: {action_type}")
        return

    # Run action in a thread to avoid blocking the tap listener
    thread = threading.Thread(target=handler, args=(value, context), daemon=True)
    thread.start()


# ---- Individual Action Handlers ----


def action_sound(value: str, context: dict):
    """Play a sound file."""
    path = value
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)

    if not os.path.exists(path):
        print(f"  ⚠️  Sound file not found: {path}")
        return

    system = sys.platform
    try:
        if system == "darwin":
            subprocess.run(["afplay", path], check=True, capture_output=True)
        elif system == "win32":
            # Use PowerShell for reliable playback
            ps_cmd = f'(New-Object Media.SoundPlayer "{path}").PlaySync()'
            subprocess.run(["powershell", "-Command", ps_cmd],
                           check=True, capture_output=True)
        else:
            # Linux — try aplay, paplay, or ffplay
            for player in ["aplay", "paplay", "ffplay -nodisp -autoexit"]:
                cmd = player.split() + [path]
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    return
                except FileNotFoundError:
                    continue
            print("  ⚠️  No audio player found. Install aplay, paplay, or ffmpeg.")
    except Exception as e:
        print(f"  ⚠️  Sound playback error: {e}")


def action_command(value: str, context: dict):
    """Run a shell command."""
    try:
        result = subprocess.run(
            value, shell=True, capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            print(f"  📋 Output: {result.stdout.strip()[:200]}")
        if result.returncode != 0 and result.stderr.strip():
            print(f"  ⚠️  Command stderr: {result.stderr.strip()[:200]}")
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  Command timed out: {value[:50]}")
    except Exception as e:
        print(f"  ⚠️  Command error: {e}")


def action_notify(value: str, context: dict):
    """Show a desktop notification."""
    title = "TapCraft"
    message = value
    system = sys.platform

    try:
        if system == "darwin":
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], capture_output=True)
        elif system == "win32":
            # Use PowerShell toast notification
            ps_cmd = f"""
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(0)
            $text = $template.GetElementsByTagName('text')
            $text[0].AppendChild($template.CreateTextNode('{title}')) | Out-Null
            $text[1].AppendChild($template.CreateTextNode('{message}')) | Out-Null
            $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('TapCraft')
            $notifier.Show([Windows.UI.Notifications.ToastNotification]::new($template))
            """
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
        else:
            subprocess.run(["notify-send", title, message], capture_output=True)
    except Exception as e:
        print(f"  📢 {title}: {message}")  # Fallback to console


def action_type_text(value: str, context: dict):
    """Type text at the current cursor position."""
    system = sys.platform

    try:
        if system == "darwin":
            # Use osascript to type text
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            script = f'tell application "System Events" to keystroke "{escaped}"'
            subprocess.run(["osascript", "-e", script], capture_output=True)
        elif system == "win32":
            # Use PowerShell SendKeys
            escaped = value.replace("{", "{{").replace("}", "}}")
            ps_cmd = f"""
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.SendKeys]::SendWait('{escaped}')
            """
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
        else:
            # Linux — use xdotool
            subprocess.run(["xdotool", "type", "--clearmodifiers", value],
                           capture_output=True)
    except Exception as e:
        print(f"  ⚠️  Type-text error: {e}")


def action_open_app(value: str, context: dict):
    """Open an application."""
    system = sys.platform

    try:
        if system == "darwin":
            subprocess.run(["open", "-a", value], capture_output=True, check=True)
        elif system == "win32":
            subprocess.run(["start", "", value], shell=True, capture_output=True)
        else:
            subprocess.Popen([value], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"  ⚠️  Could not open app '{value}': {e}")


def action_media(value: str, context: dict):
    """Control media playback."""
    system = sys.platform

    # Map action names to key codes
    if system == "darwin":
        # macOS uses NX key codes via osascript
        key_map = {
            "play-pause": 'key code 49',  # space in many players
            "next": 'key code 124 using command down',
            "prev": 'key code 123 using command down',
            "vol-up": 'key code 126',
            "vol-down": 'key code 125',
        }
        key_cmd = key_map.get(value)
        if key_cmd:
            # Use media key events via applescript
            if value == "play-pause":
                script = """
                tell application "System Events"
                    key code 16 using {command down}
                end tell
                """
            elif value == "vol-up":
                subprocess.run(
                    ["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) + 10)"],
                    capture_output=True,
                )
                return
            elif value == "vol-down":
                subprocess.run(
                    ["osascript", "-e", "set volume output volume ((output volume of (get volume settings)) - 10)"],
                    capture_output=True,
                )
                return
            else:
                script = f'tell application "System Events" to {key_cmd}'
            subprocess.run(["osascript", "-e", script], capture_output=True)

    elif system == "win32":
        # Windows media key simulation via PowerShell
        vk_map = {
            "play-pause": "0xB3",
            "next": "0xB0",
            "prev": "0xB1",
            "vol-up": "0xAF",
            "vol-down": "0xAE",
        }
        vk = vk_map.get(value)
        if vk:
            ps_cmd = f"""
            $code = {vk}
            $sig = '[DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, int dwFlags, int dwExtraInfo);'
            $key = Add-Type -MemberDefinition $sig -Name kb -Namespace Win32 -PassThru
            $key::keybd_event($code, 0, 0, 0)
            $key::keybd_event($code, 0, 2, 0)
            """
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)

    else:
        # Linux — use playerctl or xdotool
        playerctl_map = {
            "play-pause": "play-pause",
            "next": "next",
            "prev": "previous",
        }
        if value in playerctl_map:
            subprocess.run(["playerctl", playerctl_map[value]], capture_output=True)
        elif value == "vol-up":
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"],
                           capture_output=True)
        elif value == "vol-down":
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"],
                           capture_output=True)


def action_clipboard(value: str, context: dict):
    """Clipboard operations."""
    system = sys.platform

    if value == "paste-plain":
        # Get clipboard content as plain text and re-paste it
        try:
            if system == "darwin":
                result = subprocess.run(["pbpaste"], capture_output=True, text=True)
                text = result.stdout
                # Type it out instead of pasting (strips formatting)
                action_type_text(text, context)
            elif system == "win32":
                ps_cmd = "Get-Clipboard -Format Text"
                result = subprocess.run(["powershell", "-Command", ps_cmd],
                                        capture_output=True, text=True)
                action_type_text(result.stdout.strip(), context)
            else:
                result = subprocess.run(["xclip", "-selection", "clipboard", "-o"],
                                        capture_output=True, text=True)
                action_type_text(result.stdout, context)
        except Exception as e:
            print(f"  ⚠️  Clipboard error: {e}")

    elif value == "copy-line":
        # Select current line and copy
        if system == "darwin":
            script = """
            tell application "System Events"
                key code 0 using command down
                key code 0 using {command down, shift down}
                key code 8 using command down
            end tell
            """
            subprocess.run(["osascript", "-e", script], capture_output=True)


def action_script(value: str, context: dict):
    """Run a Python script / plugin file."""
    path = value
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)

    if not os.path.exists(path):
        print(f"  ⚠️  Script not found: {path}")
        return

    try:
        subprocess.run(
            [sys.executable, path],
            env={**os.environ, "TAPCRAFT_CONTEXT": str(context)},
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as e:
        print(f"  ⚠️  Script error: {e}")


# ---- Plugin Loader ----

_plugin_cache = {}


def _try_load_plugin(action_type: str):
    """Try to load a plugin action handler from the plugins/ directory."""
    if action_type in _plugin_cache:
        return _plugin_cache[action_type]

    plugins_dir = os.path.join(os.getcwd(), "plugins")
    if not os.path.isdir(plugins_dir):
        return None

    for fname in os.listdir(plugins_dir):
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(plugins_dir, fname)
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(fname[:-3], fpath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if (isinstance(attr, type)
                        and hasattr(attr, "name")
                        and hasattr(attr, "execute")
                        and getattr(attr, "name", None) == action_type):
                    instance = attr()
                    handler = instance.execute
                    _plugin_cache[action_type] = handler
                    return handler
        except Exception:
            continue

    _plugin_cache[action_type] = None
    return None


# ---- Action Registry ----

ACTION_REGISTRY = {
    "sound": action_sound,
    "command": action_command,
    "notify": action_notify,
    "type-text": action_type_text,
    "open-app": action_open_app,
    "media": action_media,
    "clipboard": action_clipboard,
    "script": action_script,
}
