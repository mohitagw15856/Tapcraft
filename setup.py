"""TapCraft — Turn your trackpad into a programmable command surface."""

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Platform-specific dependencies
install_requires = [
    "pyyaml>=6.0",
]

extras_require = {
    "macos": [
        "pyobjc-framework-Quartz>=9.0",
        "pyobjc-framework-Cocoa>=9.0",
        "rumps>=0.4.0",
    ],
    "windows": [
        "pynput>=1.7.6",
    ],
    "linux": [
        "evdev>=1.6.0",
        "pynput>=1.7.6",
    ],
    "mic": [
        "sounddevice>=0.4.6",
        "numpy>=1.24.0",
    ],
    "all": [
        "sounddevice>=0.4.6",
        "numpy>=1.24.0",
        "playsound>=1.3.0",
    ],
    "dev": [
        "pytest>=7.0",
        "ruff",
    ],
}

setup(
    name="tapcraft",
    version="0.1.0",
    description="Turn your trackpad into a programmable command surface. Assign actions to tap zones, gestures, and physical slaps.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_USERNAME/tapcraft",
    author="TapCraft Contributors",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment",
        "Topic :: Utilities",
    ],
    keywords="trackpad, gestures, macros, automation, accelerometer, slap, productivity",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "tapcraft=tapcraft:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["sounds/*.wav", "sounds/*.mp3", "config.yaml"],
    },
)
