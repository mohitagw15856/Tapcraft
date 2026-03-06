#!/usr/bin/env python3
"""TapCraft GUI Configurator — visual setup for your tap and slap actions.

Run with:
    python tapcraft_gui.py

No extra dependencies — uses tkinter which comes with Python.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yaml
import subprocess
import threading
import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# Constants
# ============================================================

ZONES = [
    "top-left", "top-mid", "top-right",
    "mid-left", "center", "mid-right",
    "bot-left", "bot-mid", "bot-right",
]

GESTURES = ["single", "double", "triple", "two-finger", "three-finger"]

ACTIONS = ["notify", "command", "open-app", "sound", "type-text", "media", "clipboard", "script"]

ACTION_DESCRIPTIONS = {
    "notify": "Show a desktop notification",
    "command": "Run a shell command (platform-specific)",
    "open-app": "Open an app by name (cross-platform)",
    "sound": "Play a .wav or .mp3 file",
    "type-text": "Type text at cursor position",
    "media": "Media control (play-pause, next, prev, vol-up, vol-down)",
    "clipboard": "Clipboard tools (paste-plain, copy-line)",
    "script": "Run a Python plugin script",
}

ZONE_GRID_POS = {
    "top-left": (0, 0), "top-mid": (0, 1), "top-right": (0, 2),
    "mid-left": (1, 0), "center": (1, 1), "mid-right": (1, 2),
    "bot-left": (2, 0), "bot-mid": (2, 1), "bot-right": (2, 2),
}

# Colors
BG = "#1a1a2e"
BG_LIGHT = "#16213e"
BG_CARD = "#0f3460"
ACCENT = "#e94560"
ACCENT_HOVER = "#ff6b6b"
TEXT = "#eaeaea"
TEXT_DIM = "#8892b0"
SUCCESS = "#64ffda"
BORDER = "#233554"


def get_config_path():
    local = os.path.join(os.getcwd(), "config.yaml")
    if os.path.exists(local):
        return local
    return local  # will create it


def load_config(path):
    if not os.path.exists(path):
        return {"settings": {"tap_timeout_ms": 300, "zone_padding": 0.05, "feedback": True, "log_taps": False},
                "slap": {"enabled": False}, "mappings": {}}
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    return data


def save_config(path, config):
    with open(path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


# ============================================================
# Main GUI Application
# ============================================================

class TapCraftGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TapCraft Configurator")
        self.root.geometry("900x700")
        self.root.configure(bg=BG)
        self.root.minsize(800, 600)

        self.config_path = get_config_path()
        self.config = load_config(self.config_path)
        self.tapcraft_process = None

        # Ensure config has required sections
        if "mappings" not in self.config:
            self.config["mappings"] = {}
        if "settings" not in self.config:
            self.config["settings"] = {}
        if "slap" not in self.config:
            self.config["slap"] = {"enabled": False}

        self._build_ui()

    def _build_ui(self):
        # --- Header ---
        header = tk.Frame(self.root, bg=BG, pady=10)
        header.pack(fill="x", padx=20)

        tk.Label(header, text="TapCraft", font=("Segoe UI", 24, "bold"),
                 fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(header, text="  Configurator", font=("Segoe UI", 24),
                 fg=TEXT_DIM, bg=BG).pack(side="left")

        # Status indicator
        self.status_frame = tk.Frame(header, bg=BG)
        self.status_frame.pack(side="right")
        self.status_dot = tk.Label(self.status_frame, text="\u25cf", font=("Segoe UI", 14),
                                   fg=TEXT_DIM, bg=BG)
        self.status_dot.pack(side="left")
        self.status_label = tk.Label(self.status_frame, text="Stopped",
                                     font=("Segoe UI", 10), fg=TEXT_DIM, bg=BG)
        self.status_label.pack(side="left", padx=(4, 0))

        # --- Notebook (tabs) ---
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_LIGHT, foreground=TEXT,
                        padding=[16, 8], font=("Segoe UI", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", BG_CARD)],
                  foreground=[("selected", ACCENT)])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Tab 1: Zone Grid
        self.grid_tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.grid_tab, text="  Trackpad Zones  ")
        self._build_grid_tab()

        # Tab 2: Slap Config
        self.slap_tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.slap_tab, text="  Slap Detection  ")
        self._build_slap_tab()

        # Tab 3: Settings
        self.settings_tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.settings_tab, text="  Settings  ")
        self._build_settings_tab()

        # --- Bottom Bar ---
        bottom = tk.Frame(self.root, bg=BG_LIGHT, pady=12)
        bottom.pack(fill="x", side="bottom")

        self.start_btn = tk.Button(
            bottom, text="\u25b6  Start TapCraft", font=("Segoe UI", 11, "bold"),
            bg=SUCCESS, fg="#1a1a2e", activebackground=ACCENT_HOVER,
            relief="flat", padx=20, pady=6, cursor="hand2",
            command=self._toggle_tapcraft
        )
        self.start_btn.pack(side="right", padx=20)

        tk.Button(
            bottom, text="Save Config", font=("Segoe UI", 10),
            bg=BG_CARD, fg=TEXT, activebackground=ACCENT,
            relief="flat", padx=16, pady=6, cursor="hand2",
            command=self._save
        ).pack(side="right", padx=4)

        self.config_label = tk.Label(
            bottom, text=f"Config: {self.config_path}",
            font=("Segoe UI", 9), fg=TEXT_DIM, bg=BG_LIGHT
        )
        self.config_label.pack(side="left", padx=20)

    # ============================================================
    # Tab 1: Trackpad Zone Grid
    # ============================================================

    def _build_grid_tab(self):
        tk.Label(self.grid_tab, text="Click a zone to configure its actions",
                 font=("Segoe UI", 10), fg=TEXT_DIM, bg=BG).pack(pady=(12, 8))

        # Platform note
        if sys.platform == "win32":
            note = "Windows: zones map to screen regions + Ctrl+Alt+Numpad 1-9 hotkeys"
        elif sys.platform == "darwin":
            note = "macOS: zones map to physical trackpad touch positions"
        else:
            note = "Linux: zones map to trackpad touch positions via evdev"
        tk.Label(self.grid_tab, text=note,
                 font=("Segoe UI", 9), fg=ACCENT, bg=BG).pack(pady=(0, 12))

        # 3x3 Grid
        grid_frame = tk.Frame(self.grid_tab, bg=BORDER, padx=3, pady=3)
        grid_frame.pack(expand=True)

        self.zone_buttons = {}
        for zone, (row, col) in ZONE_GRID_POS.items():
            btn_frame = tk.Frame(grid_frame, bg=BORDER)
            btn_frame.grid(row=row, column=col, padx=2, pady=2)

            # Count configured gestures
            zone_config = self.config.get("mappings", {}).get(zone, {})
            count = len(zone_config)

            bg_color = BG_CARD if count > 0 else BG_LIGHT
            count_text = f"\n{count} action{'s' if count != 1 else ''}" if count > 0 else "\nno actions"
            count_fg = SUCCESS if count > 0 else TEXT_DIM

            btn = tk.Button(
                btn_frame, text=f"{zone}{count_text}",
                font=("Segoe UI", 10), fg=TEXT, bg=bg_color,
                activebackground=ACCENT, activeforeground="white",
                relief="flat", width=16, height=4, cursor="hand2",
                command=lambda z=zone: self._edit_zone(z)
            )
            btn.pack()
            self.zone_buttons[zone] = btn

    def _edit_zone(self, zone):
        """Open a dialog to edit actions for a zone."""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Configure: {zone}")
        dialog.geometry("500x520")
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"Zone: {zone}", font=("Segoe UI", 16, "bold"),
                 fg=ACCENT, bg=BG).pack(pady=(16, 4))
        tk.Label(dialog, text="Configure actions for each gesture type",
                 font=("Segoe UI", 9), fg=TEXT_DIM, bg=BG).pack(pady=(0, 12))

        zone_config = self.config.get("mappings", {}).get(zone, {})
        entries = {}

        canvas = tk.Canvas(dialog, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for gesture in GESTURES:
            frame = tk.LabelFrame(scroll_frame, text=f"  {gesture}  ",
                                  font=("Segoe UI", 10, "bold"),
                                  fg=TEXT, bg=BG_LIGHT, labelanchor="nw",
                                  padx=10, pady=8, relief="flat", bd=1)
            frame.pack(fill="x", padx=16, pady=4)

            current = zone_config.get(gesture, {})

            # Action type dropdown
            row1 = tk.Frame(frame, bg=BG_LIGHT)
            row1.pack(fill="x", pady=2)
            tk.Label(row1, text="Action:", font=("Segoe UI", 9),
                     fg=TEXT_DIM, bg=BG_LIGHT, width=8, anchor="w").pack(side="left")
            action_var = tk.StringVar(value=current.get("action", ""))
            action_menu = ttk.Combobox(row1, textvariable=action_var,
                                       values=["(none)"] + ACTIONS, width=14, state="readonly")
            action_menu.pack(side="left", padx=4)
            if not current:
                action_var.set("(none)")

            # Value entry
            row2 = tk.Frame(frame, bg=BG_LIGHT)
            row2.pack(fill="x", pady=2)
            tk.Label(row2, text="Value:", font=("Segoe UI", 9),
                     fg=TEXT_DIM, bg=BG_LIGHT, width=8, anchor="w").pack(side="left")
            value_var = tk.StringVar(value=current.get("value", ""))
            tk.Entry(row2, textvariable=value_var, width=30,
                     font=("Segoe UI", 9)).pack(side="left", padx=4)

            # Label entry
            row3 = tk.Frame(frame, bg=BG_LIGHT)
            row3.pack(fill="x", pady=2)
            tk.Label(row3, text="Label:", font=("Segoe UI", 9),
                     fg=TEXT_DIM, bg=BG_LIGHT, width=8, anchor="w").pack(side="left")
            label_var = tk.StringVar(value=current.get("label", ""))
            tk.Entry(row3, textvariable=label_var, width=30,
                     font=("Segoe UI", 9)).pack(side="left", padx=4)

            entries[gesture] = (action_var, value_var, label_var)

        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0))
        scrollbar.pack(side="right", fill="y")

        # Save button
        def save_zone():
            if zone not in self.config.get("mappings", {}):
                self.config["mappings"][zone] = {}

            for gesture, (a_var, v_var, l_var) in entries.items():
                action = a_var.get()
                value = v_var.get().strip()
                label = l_var.get().strip()

                if action and action != "(none)" and value:
                    self.config["mappings"][zone][gesture] = {
                        "action": action,
                        "value": value,
                        "label": label or f"{zone} {gesture}",
                    }
                else:
                    # Remove if cleared
                    self.config.get("mappings", {}).get(zone, {}).pop(gesture, None)

            # Clean up empty zones
            if zone in self.config.get("mappings", {}) and not self.config["mappings"][zone]:
                del self.config["mappings"][zone]

            dialog.destroy()
            self._refresh_grid()

        btn_frame = tk.Frame(dialog, bg=BG)
        btn_frame.pack(fill="x", pady=10)
        tk.Button(btn_frame, text="Save Zone", font=("Segoe UI", 10, "bold"),
                  bg=SUCCESS, fg="#1a1a2e", relief="flat", padx=20, pady=6,
                  cursor="hand2", command=save_zone).pack(side="right", padx=20)
        tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 10),
                  bg=BG_CARD, fg=TEXT, relief="flat", padx=16, pady=6,
                  cursor="hand2", command=dialog.destroy).pack(side="right")

    def _refresh_grid(self):
        """Refresh zone button labels after config changes."""
        for zone, btn in self.zone_buttons.items():
            zone_config = self.config.get("mappings", {}).get(zone, {})
            count = len(zone_config)
            bg_color = BG_CARD if count > 0 else BG_LIGHT
            count_text = f"\n{count} action{'s' if count != 1 else ''}" if count > 0 else "\nno actions"
            btn.configure(text=f"{zone}{count_text}", bg=bg_color)

    # ============================================================
    # Tab 2: Slap Detection
    # ============================================================

    def _build_slap_tab(self):
        container = tk.Frame(self.slap_tab, bg=BG, padx=30, pady=16)
        container.pack(fill="both", expand=True)

        slap_config = self.config.get("slap", {})

        # Enable toggle
        self.slap_enabled_var = tk.BooleanVar(value=slap_config.get("enabled", False))
        tk.Checkbutton(container, text="Enable Slap Detection",
                       variable=self.slap_enabled_var, font=("Segoe UI", 12, "bold"),
                       fg=TEXT, bg=BG, selectcolor=BG_LIGHT, activebackground=BG,
                       activeforeground=TEXT).pack(anchor="w", pady=(0, 4))

        # Platform note
        if sys.platform == "win32":
            method_note = "Windows: uses microphone. Install first: pip install sounddevice numpy --only-binary=:all:"
        elif sys.platform == "darwin":
            method_note = "macOS Apple Silicon: uses accelerometer (run with sudo). Intel: uses microphone."
        else:
            method_note = "Linux: uses microphone. Install first: pip install sounddevice numpy"
        tk.Label(container, text=method_note, font=("Segoe UI", 9),
                 fg=ACCENT, bg=BG, wraplength=600, justify="left").pack(anchor="w", pady=(0, 16))

        # Method
        method_frame = tk.Frame(container, bg=BG)
        method_frame.pack(fill="x", pady=4)
        tk.Label(method_frame, text="Method:", font=("Segoe UI", 10),
                 fg=TEXT, bg=BG, width=14, anchor="w").pack(side="left")
        self.slap_method_var = tk.StringVar(value=slap_config.get("method", "auto"))
        ttk.Combobox(method_frame, textvariable=self.slap_method_var,
                     values=["auto", "accelerometer", "microphone"],
                     width=18, state="readonly").pack(side="left")

        # Sensitivity
        sens_frame = tk.Frame(container, bg=BG)
        sens_frame.pack(fill="x", pady=4)
        tk.Label(sens_frame, text="Sensitivity:", font=("Segoe UI", 10),
                 fg=TEXT, bg=BG, width=14, anchor="w").pack(side="left")
        mic_thresh = slap_config.get("microphone", {}).get("threshold", 0.3)
        self.slap_sens_var = tk.DoubleVar(value=mic_thresh)
        tk.Scale(sens_frame, from_=0.05, to=0.8, resolution=0.05, orient="horizontal",
                 variable=self.slap_sens_var, length=200, bg=BG, fg=TEXT,
                 highlightthickness=0, troughcolor=BG_LIGHT).pack(side="left")
        tk.Label(sens_frame, text="(lower = more sensitive)", font=("Segoe UI", 8),
                 fg=TEXT_DIM, bg=BG).pack(side="left", padx=8)

        # Cooldown
        cool_frame = tk.Frame(container, bg=BG)
        cool_frame.pack(fill="x", pady=4)
        tk.Label(cool_frame, text="Cooldown (ms):", font=("Segoe UI", 10),
                 fg=TEXT, bg=BG, width=14, anchor="w").pack(side="left")
        self.slap_cooldown_var = tk.IntVar(value=slap_config.get("cooldown_ms", 750))
        tk.Entry(cool_frame, textvariable=self.slap_cooldown_var, width=8,
                 font=("Segoe UI", 10)).pack(side="left")

        # Escalation
        esc_config = slap_config.get("escalation", {})
        self.escalation_var = tk.BooleanVar(value=esc_config.get("enabled", False))
        tk.Checkbutton(container, text="Escalation Mode (more slaps = crazier responses)",
                       variable=self.escalation_var, font=("Segoe UI", 10),
                       fg=TEXT, bg=BG, selectcolor=BG_LIGHT, activebackground=BG,
                       activeforeground=TEXT).pack(anchor="w", pady=(16, 4))

        # Slap action mappings
        tk.Label(container, text="Slap Strength Actions:",
                 font=("Segoe UI", 11, "bold"), fg=TEXT, bg=BG).pack(anchor="w", pady=(16, 8))

        slap_mappings = slap_config.get("mappings", {})
        self.slap_entries = {}

        for strength in ["light", "medium", "hard", "brutal", "any"]:
            row = tk.Frame(container, bg=BG_LIGHT, padx=8, pady=6)
            row.pack(fill="x", pady=2)

            current = slap_mappings.get(strength, {})

            tk.Label(row, text=f"{strength:>8}:", font=("Segoe UI", 10, "bold"),
                     fg=ACCENT if strength != "any" else SUCCESS, bg=BG_LIGHT,
                     width=8, anchor="e").pack(side="left")

            a_var = tk.StringVar(value=current.get("action", "notify"))
            ttk.Combobox(row, textvariable=a_var, values=ACTIONS,
                         width=10, state="readonly").pack(side="left", padx=4)

            v_var = tk.StringVar(value=current.get("value", ""))
            tk.Entry(row, textvariable=v_var, width=30, font=("Segoe UI", 9)).pack(side="left", padx=4)

            self.slap_entries[strength] = (a_var, v_var)

    # ============================================================
    # Tab 3: Settings
    # ============================================================

    def _build_settings_tab(self):
        container = tk.Frame(self.settings_tab, bg=BG, padx=30, pady=20)
        container.pack(fill="both", expand=True)

        settings = self.config.get("settings", {})

        tk.Label(container, text="General Settings",
                 font=("Segoe UI", 14, "bold"), fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 16))

        # Tap timeout
        row1 = tk.Frame(container, bg=BG)
        row1.pack(fill="x", pady=6)
        tk.Label(row1, text="Tap timeout (ms):", font=("Segoe UI", 10),
                 fg=TEXT, bg=BG, width=20, anchor="w").pack(side="left")
        self.timeout_var = tk.IntVar(value=settings.get("tap_timeout_ms", 300))
        tk.Entry(row1, textvariable=self.timeout_var, width=8,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Label(row1, text="Max ms between taps for double/triple detection",
                 font=("Segoe UI", 8), fg=TEXT_DIM, bg=BG).pack(side="left", padx=12)

        # Zone padding
        row2 = tk.Frame(container, bg=BG)
        row2.pack(fill="x", pady=6)
        tk.Label(row2, text="Zone padding:", font=("Segoe UI", 10),
                 fg=TEXT, bg=BG, width=20, anchor="w").pack(side="left")
        self.padding_var = tk.DoubleVar(value=settings.get("zone_padding", 0.05))
        tk.Scale(row2, from_=0.0, to=0.15, resolution=0.01, orient="horizontal",
                 variable=self.padding_var, length=150, bg=BG, fg=TEXT,
                 highlightthickness=0, troughcolor=BG_LIGHT).pack(side="left")

        # Feedback
        self.feedback_var = tk.BooleanVar(value=settings.get("feedback", True))
        tk.Checkbutton(container, text="Show feedback when actions trigger",
                       variable=self.feedback_var, font=("Segoe UI", 10),
                       fg=TEXT, bg=BG, selectcolor=BG_LIGHT,
                       activebackground=BG, activeforeground=TEXT).pack(anchor="w", pady=8)

        # Log taps
        self.log_var = tk.BooleanVar(value=settings.get("log_taps", False))
        tk.Checkbutton(container, text="Log all taps to console (debugging)",
                       variable=self.log_var, font=("Segoe UI", 10),
                       fg=TEXT, bg=BG, selectcolor=BG_LIGHT,
                       activebackground=BG, activeforeground=TEXT).pack(anchor="w", pady=4)

        # Config file location
        tk.Label(container, text="Config File",
                 font=("Segoe UI", 14, "bold"), fg=TEXT, bg=BG).pack(anchor="w", pady=(24, 8))

        path_frame = tk.Frame(container, bg=BG)
        path_frame.pack(fill="x", pady=4)
        tk.Label(path_frame, text=self.config_path, font=("Consolas", 9),
                 fg=SUCCESS, bg=BG).pack(side="left")

        # Platform info
        tk.Label(container, text="Platform Info",
                 font=("Segoe UI", 14, "bold"), fg=TEXT, bg=BG).pack(anchor="w", pady=(24, 8))

        platform = sys.platform
        platform_name = {"darwin": "macOS", "win32": "Windows", "linux": "Linux"}.get(platform, platform)
        tk.Label(container, text=f"Detected: {platform_name} ({platform})",
                 font=("Segoe UI", 10), fg=TEXT, bg=BG).pack(anchor="w")

        if platform == "win32":
            info = "Input: screen grid + Ctrl+Alt+Numpad hotkeys. Slap: microphone."
        elif platform == "darwin":
            info = "Input: trackpad multi-touch. Slap: accelerometer (M2+) or microphone."
        else:
            info = "Input: trackpad evdev. Slap: microphone."
        tk.Label(container, text=info, font=("Segoe UI", 9),
                 fg=TEXT_DIM, bg=BG, wraplength=500, justify="left").pack(anchor="w", pady=4)

    # ============================================================
    # Save / Run
    # ============================================================

    def _save(self):
        """Collect all GUI state and save to config.yaml."""
        # Settings
        self.config["settings"] = {
            "tap_timeout_ms": self.timeout_var.get(),
            "zone_padding": self.padding_var.get(),
            "feedback": self.feedback_var.get(),
            "log_taps": self.log_var.get(),
        }

        # Slap config
        slap = self.config.get("slap", {})
        slap["enabled"] = self.slap_enabled_var.get()
        slap["method"] = self.slap_method_var.get()
        slap["cooldown_ms"] = self.slap_cooldown_var.get()

        if "microphone" not in slap:
            slap["microphone"] = {}
        slap["microphone"]["threshold"] = self.slap_sens_var.get()

        if "escalation" not in slap:
            slap["escalation"] = {}
        slap["escalation"]["enabled"] = self.escalation_var.get()

        # Slap mappings
        if "mappings" not in slap:
            slap["mappings"] = {}
        for strength, (a_var, v_var) in self.slap_entries.items():
            action = a_var.get()
            value = v_var.get().strip()
            if action and value:
                slap["mappings"][strength] = {
                    "action": action,
                    "value": value,
                    "label": f"{strength.title()} slap",
                }

        self.config["slap"] = slap

        # Save to file
        save_config(self.config_path, self.config)
        messagebox.showinfo("Saved", f"Config saved to:\n{self.config_path}")

    def _toggle_tapcraft(self):
        """Start or stop TapCraft."""
        if self.tapcraft_process and self.tapcraft_process.poll() is None:
            # Stop
            self.tapcraft_process.terminate()
            self.tapcraft_process = None
            self.start_btn.configure(text="\u25b6  Start TapCraft", bg=SUCCESS)
            self.status_dot.configure(fg=TEXT_DIM)
            self.status_label.configure(text="Stopped", fg=TEXT_DIM)
        else:
            # Save first
            self._save()

            # Start
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tapcraft.py")
            cmd = [sys.executable, script, "--log"]

            try:
                self.tapcraft_process = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
                )
                self.start_btn.configure(text="\u25a0  Stop TapCraft", bg=ACCENT)
                self.status_dot.configure(fg=SUCCESS)
                self.status_label.configure(text="Running", fg=SUCCESS)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start TapCraft:\n{e}")

    def on_close(self):
        """Clean up when window closes."""
        if self.tapcraft_process and self.tapcraft_process.poll() is None:
            self.tapcraft_process.terminate()
        self.root.destroy()


# ============================================================
# Main
# ============================================================

def main():
    root = tk.Tk()
    app = TapCraftGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
