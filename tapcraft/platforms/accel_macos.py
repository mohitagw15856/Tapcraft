"""macOS accelerometer-based slap detection via IOKit HID.

This module reads the Apple Silicon MEMS accelerometer (Bosch BMI286 IMU)
directly through IOKit HID to detect physical impacts on the laptop body.
Inspired by taigrr/spank and olvvier/apple-silicon-accelerometer.

Requirements:
- macOS on Apple Silicon (M2+)
- Must run with sudo (IOKit HID access requires root)
- pyobjc-framework-Quartz

The sensor lives under AppleSPUHIDDevice in the IOKit registry at
vendor usage page 0xFF00, usage 3. It sends 22-byte HID reports
containing int32 x/y/z acceleration values at offsets 6, 10, 14.
Divide by 65536 to get acceleration in g-force units.
"""

import sys
import struct
import time
import math
import ctypes
import ctypes.util
from collections import deque
from typing import Callable, Optional

if sys.platform != "darwin":
    raise ImportError("Accelerometer slap detection only works on macOS Apple Silicon")


# ---------------------------------------------------------------------------
# IOKit / CoreFoundation ctypes bindings (minimal set for HID access)
# ---------------------------------------------------------------------------

def _load_framework(name):
    path = ctypes.util.find_library(name)
    if path:
        return ctypes.cdll.LoadLibrary(path)
    raise OSError(f"Cannot find framework: {name}")


_iokit = _load_framework("IOKit")
_cf = _load_framework("CoreFoundation")

# CoreFoundation types
CFAllocatorRef = ctypes.c_void_p
CFDictionaryRef = ctypes.c_void_p
CFStringRef = ctypes.c_void_p
CFNumberRef = ctypes.c_void_p
CFRunLoopRef = ctypes.c_void_p
CFRunLoopSourceRef = ctypes.c_void_p

kCFAllocatorDefault = None
kCFNumberSInt32Type = 3

# IOKit types
IOHIDManagerRef = ctypes.c_void_p
IOHIDDeviceRef = ctypes.c_void_p

# IOKit HID Report callback signature
IOHIDReportCallback = ctypes.CFUNCTYPE(
    None,                    # return void
    ctypes.c_void_p,         # context
    ctypes.c_int32,          # result (IOReturn)
    ctypes.c_void_p,         # sender
    ctypes.c_int32,          # type (IOHIDReportType)
    ctypes.c_uint32,         # reportID
    ctypes.POINTER(ctypes.c_uint8),  # report
    ctypes.c_int32,          # reportLength
)

# Function signatures
_cf.CFRunLoopGetCurrent.restype = CFRunLoopRef
_cf.CFStringCreateWithCString.restype = CFStringRef
_cf.CFStringCreateWithCString.argtypes = [CFAllocatorRef, ctypes.c_char_p, ctypes.c_uint32]
_cf.CFNumberCreate.restype = CFNumberRef
_cf.CFNumberCreate.argtypes = [CFAllocatorRef, ctypes.c_int32, ctypes.c_void_p]
_cf.CFDictionaryCreateMutable.restype = CFDictionaryRef
_cf.CFDictionarySetValue.argtypes = [CFDictionaryRef, ctypes.c_void_p, ctypes.c_void_p]
_cf.CFRelease.argtypes = [ctypes.c_void_p]

_iokit.IOHIDManagerCreate.restype = IOHIDManagerRef
_iokit.IOHIDManagerCreate.argtypes = [CFAllocatorRef, ctypes.c_uint32]
_iokit.IOHIDManagerSetDeviceMatching.argtypes = [IOHIDManagerRef, CFDictionaryRef]
_iokit.IOHIDManagerOpen.argtypes = [IOHIDManagerRef, ctypes.c_uint32]
_iokit.IOHIDManagerOpen.restype = ctypes.c_int32
_iokit.IOHIDManagerCopyDevices.restype = ctypes.c_void_p
_iokit.IOHIDManagerScheduleWithRunLoop.argtypes = [
    IOHIDManagerRef, CFRunLoopRef, CFStringRef
]
_iokit.IOHIDManagerRegisterInputReportCallback.argtypes = [
    IOHIDManagerRef, IOHIDReportCallback, ctypes.c_void_p
]

kCFStringEncodingUTF8 = 0x08000100
kIOHIDOptionsTypeNone = 0

# kCFRunLoopDefaultMode string
_kCFRunLoopDefaultMode = _cf.CFStringCreateWithCString(
    kCFAllocatorDefault, b"kCFRunLoopDefaultMode", kCFStringEncodingUTF8
)


def _cfstr(s: str) -> CFStringRef:
    return _cf.CFStringCreateWithCString(kCFAllocatorDefault, s.encode(), kCFStringEncodingUTF8)


def _cfnum(val: int) -> CFNumberRef:
    v = ctypes.c_int32(val)
    return _cf.CFNumberCreate(kCFAllocatorDefault, kCFNumberSInt32Type, ctypes.byref(v))


# ---------------------------------------------------------------------------
# Accelerometer sample and detection
# ---------------------------------------------------------------------------

class AccelSample:
    """A single accelerometer reading."""
    __slots__ = ("x", "y", "z", "t", "magnitude")

    def __init__(self, x: float, y: float, z: float, t: float):
        self.x = x
        self.y = y
        self.z = z
        self.t = t
        # Dynamic magnitude: subtract ~1g gravity from total magnitude
        total = math.sqrt(x * x + y * y + z * z)
        self.magnitude = abs(total - 1.0)  # at rest this should be ~0


class SlapDetector:
    """Detects physical impacts from accelerometer data.

    Uses a combination of:
    - Short-term average / Long-term average (STA/LTA) ratio
    - Amplitude threshold
    - Cooldown period to prevent rapid-fire triggers

    This is a simplified version of the vibration detection pipeline
    used by olvvier/apple-silicon-accelerometer and taigrr/spank.
    """

    def __init__(
        self,
        min_amplitude: float = 0.15,
        sta_window: int = 10,
        lta_window: int = 100,
        sta_lta_threshold: float = 3.0,
        cooldown_ms: int = 750,
        on_slap: Optional[Callable] = None,
    ):
        self.min_amplitude = min_amplitude
        self.sta_window = sta_window
        self.lta_window = lta_window
        self.sta_lta_threshold = sta_lta_threshold
        self.cooldown_ms = cooldown_ms
        self.on_slap = on_slap

        self._sta_buffer = deque(maxlen=sta_window)
        self._lta_buffer = deque(maxlen=lta_window)
        self._last_trigger_time = 0.0
        self._sample_count = 0

    def feed(self, sample: AccelSample):
        """Feed an accelerometer sample into the detector."""
        mag = sample.magnitude
        self._sta_buffer.append(mag)
        self._lta_buffer.append(mag)
        self._sample_count += 1

        # Need enough samples for detection
        if self._sample_count < self.lta_window:
            return

        # Compute STA/LTA ratio
        sta = sum(self._sta_buffer) / len(self._sta_buffer)
        lta = sum(self._lta_buffer) / len(self._lta_buffer)

        if lta < 0.001:
            lta = 0.001  # Prevent division by zero

        ratio = sta / lta

        # Check if we have a slap
        if mag >= self.min_amplitude and ratio >= self.sta_lta_threshold:
            now = time.time()
            elapsed_ms = (now - self._last_trigger_time) * 1000

            if elapsed_ms >= self.cooldown_ms:
                self._last_trigger_time = now

                slap_info = {
                    "amplitude": mag,
                    "sta_lta_ratio": ratio,
                    "peak_g": math.sqrt(
                        sample.x ** 2 + sample.y ** 2 + sample.z ** 2
                    ),
                    "timestamp": sample.t,
                    # Classify strength
                    "strength": self._classify_strength(mag),
                }

                if self.on_slap:
                    self.on_slap(slap_info)

    @staticmethod
    def _classify_strength(amplitude: float) -> str:
        """Classify the slap strength for user-friendly labeling."""
        if amplitude < 0.2:
            return "light"
        elif amplitude < 0.5:
            return "medium"
        elif amplitude < 1.0:
            return "hard"
        else:
            return "brutal"


# ---------------------------------------------------------------------------
# IOKit HID listener
# ---------------------------------------------------------------------------

def start_accelerometer_listener(
    on_slap: Callable,
    min_amplitude: float = 0.15,
    cooldown_ms: int = 750,
):
    """Start reading the Apple Silicon accelerometer and detecting slaps.

    Args:
        on_slap: Callback function receiving a slap_info dict.
        min_amplitude: Minimum amplitude (in g) to trigger. Lower = more sensitive.
        cooldown_ms: Minimum ms between triggers.

    Note: Must be run with sudo!
    """
    import os
    if os.geteuid() != 0:
        print("❌ Accelerometer access requires root privileges.")
        print("   Run with: sudo python tapcraft.py --slap")
        return

    detector = SlapDetector(
        min_amplitude=min_amplitude,
        cooldown_ms=cooldown_ms,
        on_slap=on_slap,
    )

    # Create HID Manager
    manager = _iokit.IOHIDManagerCreate(kCFAllocatorDefault, kIOHIDOptionsTypeNone)

    # Match the AppleSPU accelerometer device
    # Vendor usage page 0xFF00, usage 3
    match_dict = _cf.CFDictionaryCreateMutable(
        kCFAllocatorDefault, 2, None, None
    )
    _cf.CFDictionarySetValue(match_dict, _cfstr("PrimaryUsagePage"), _cfnum(0xFF00))
    _cf.CFDictionarySetValue(match_dict, _cfstr("PrimaryUsage"), _cfnum(3))

    _iokit.IOHIDManagerSetDeviceMatching(manager, match_dict)

    result = _iokit.IOHIDManagerOpen(manager, kIOHIDOptionsTypeNone)
    if result != 0:
        print(f"❌ Failed to open HID Manager (error: {result})")
        print("   Make sure you're on Apple Silicon (M2+) and running with sudo.")
        return

    # Check if we got any matching devices
    device_set = _iokit.IOHIDManagerCopyDevices(manager)
    if not device_set:
        print("❌ No accelerometer device found.")
        print("   This feature requires Apple Silicon (M2+).")
        return

    print("  📡 Accelerometer device found!")

    # Register the report callback
    def _report_callback(context, result, sender, report_type, report_id, report, length):
        """Parse 22-byte HID reports into acceleration samples."""
        try:
            if length == 22:
                data = bytes(report[:22])
                # x/y/z are int32 at offsets 6, 10, 14
                x = struct.unpack("<i", data[6:10])[0] / 65536.0
                y = struct.unpack("<i", data[10:14])[0] / 65536.0
                z = struct.unpack("<i", data[14:18])[0] / 65536.0

                sample = AccelSample(x=x, y=y, z=z, t=time.time())
                detector.feed(sample)
        except Exception:
            pass  # Don't crash on malformed reports

    # Must keep a reference to prevent garbage collection
    _callback_ref = IOHIDReportCallback(_report_callback)

    _iokit.IOHIDManagerRegisterInputReportCallback(
        manager, _callback_ref, None
    )

    # Schedule with run loop
    run_loop = _cf.CFRunLoopGetCurrent()
    _iokit.IOHIDManagerScheduleWithRunLoop(
        manager, run_loop, _kCFRunLoopDefaultMode
    )

    print("  🖐️  Slap detection active! Hit your laptop to trigger actions.")
    print(f"  ⚙️  Sensitivity: {min_amplitude}g | Cooldown: {cooldown_ms}ms\n")

    # Run the event loop
    _cf.CFRunLoopRun()
