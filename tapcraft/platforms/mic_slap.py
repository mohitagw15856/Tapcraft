"""Microphone-based slap/impact detection — cross-platform fallback.

When the accelerometer isn't available (non-Apple-Silicon Macs, Windows,
Linux), we can detect slaps and hits by listening for sudden loud sounds
through the built-in microphone. This is inspired by albertofwb's
cross-platform fork of spank.

The microphone picks up the sharp percussive sound of a slap or hit
on the laptop body surprisingly well. We use a simple amplitude
threshold with noise floor adaptation.

Requirements:
- sounddevice (pip install sounddevice)
- numpy
"""

import time
import math
import threading
from collections import deque
from typing import Callable, Optional


def _check_dependencies():
    """Check that sounddevice and numpy are available."""
    try:
        import sounddevice  # noqa: F401
        import numpy  # noqa: F401
        return True
    except ImportError:
        return False


class MicSlapDetector:
    """Detects physical impacts via microphone audio amplitude.

    Continuously monitors the default input device and triggers
    when a sudden loud sound exceeds the adaptive threshold.
    """

    def __init__(
        self,
        threshold: float = 0.3,
        cooldown_ms: int = 750,
        noise_floor_window: int = 50,
        spike_ratio: float = 4.0,
        on_slap: Optional[Callable] = None,
    ):
        """
        Args:
            threshold: Absolute amplitude threshold (0.0 - 1.0).
            cooldown_ms: Minimum ms between triggers.
            noise_floor_window: Number of chunks to average for noise floor.
            spike_ratio: How many times above noise floor to trigger.
            on_slap: Callback function receiving a slap_info dict.
        """
        self.threshold = threshold
        self.cooldown_ms = cooldown_ms
        self.noise_floor_window = noise_floor_window
        self.spike_ratio = spike_ratio
        self.on_slap = on_slap

        self._noise_floor_buffer = deque(maxlen=noise_floor_window)
        self._last_trigger_time = 0.0
        self._running = False

    def start(self):
        """Start listening on the microphone."""
        if not _check_dependencies():
            print("❌ Microphone slap detection requires: sounddevice, numpy")
            print("   Run: pip install sounddevice numpy")
            return

        import sounddevice as sd
        import numpy as np

        self._running = True

        # Audio parameters
        sample_rate = 44100
        block_size = 1024  # ~23ms chunks at 44.1kHz

        print("  🎤 Microphone slap detection starting...")

        try:
            device_info = sd.query_devices(kind="input")
            print(f"  📱 Input device: {device_info['name']}")
        except Exception:
            print("  📱 Using default input device")

        print(f"  ⚙️  Threshold: {self.threshold} | Spike ratio: {self.spike_ratio}x")
        print(f"  ⚙️  Cooldown: {self.cooldown_ms}ms\n")

        def audio_callback(indata, frames, time_info, status):
            """Process each audio chunk."""
            if not self._running:
                return

            if status:
                pass  # Ignore overflow warnings

            # Compute RMS amplitude
            rms = float(np.sqrt(np.mean(indata ** 2)))
            peak = float(np.max(np.abs(indata)))

            # Update noise floor
            self._noise_floor_buffer.append(rms)

            # Need some baseline data first
            if len(self._noise_floor_buffer) < 10:
                return

            # Compute adaptive noise floor
            noise_floor = sum(self._noise_floor_buffer) / len(self._noise_floor_buffer)

            # Check for spike
            is_above_threshold = peak >= self.threshold
            is_spike = rms > (noise_floor * self.spike_ratio) if noise_floor > 0.001 else False

            if is_above_threshold or is_spike:
                now = time.time()
                elapsed_ms = (now - self._last_trigger_time) * 1000

                if elapsed_ms >= self.cooldown_ms:
                    self._last_trigger_time = now

                    # Classify strength based on peak
                    if peak < 0.3:
                        strength = "light"
                    elif peak < 0.6:
                        strength = "medium"
                    elif peak < 0.85:
                        strength = "hard"
                    else:
                        strength = "brutal"

                    slap_info = {
                        "amplitude": peak,
                        "rms": rms,
                        "noise_floor": noise_floor,
                        "spike_ratio": rms / noise_floor if noise_floor > 0.001 else 0,
                        "timestamp": now,
                        "strength": strength,
                        "source": "microphone",
                    }

                    if self.on_slap:
                        self.on_slap(slap_info)

                    # Don't include this spike in the noise floor
                    if self._noise_floor_buffer:
                        self._noise_floor_buffer.pop()

        # Start the audio stream
        try:
            with sd.InputStream(
                samplerate=sample_rate,
                blocksize=block_size,
                channels=1,
                callback=audio_callback,
            ):
                print("  🖐️  Microphone slap detection active! Hit your laptop.\n")
                while self._running:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            self._running = False
        except Exception as e:
            print(f"❌ Microphone error: {e}")
            print("   Make sure a microphone is available and accessible.")

    def stop(self):
        """Stop listening."""
        self._running = False


def start_mic_listener(
    on_slap: Callable,
    threshold: float = 0.3,
    cooldown_ms: int = 750,
):
    """Start microphone-based slap detection.

    Args:
        on_slap: Callback receiving slap_info dict.
        threshold: Amplitude threshold (0.0-1.0). Lower = more sensitive.
        cooldown_ms: Minimum ms between triggers.
    """
    detector = MicSlapDetector(
        threshold=threshold,
        cooldown_ms=cooldown_ms,
        on_slap=on_slap,
    )
    detector.start()
