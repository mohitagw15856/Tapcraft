# Changelog

All notable changes to TapCraft will be documented in this file.

## [0.1.0] — 2026-03-06

### Added
- Initial release
- 3x3 trackpad zone detection with configurable dead zones
- Gesture recognition: single, double, triple, two-finger, three-finger taps
- 8 built-in action types: sound, command, notify, type-text, open-app, media, clipboard, script
- Slap/hit detection via Apple Silicon accelerometer (macOS M2+, requires sudo)
- Slap/hit detection via microphone (cross-platform fallback)
- Strength-based slap actions: light, medium, hard, brutal
- Escalation mode: cumulative slap frequency triggers escalating responses
- Plugin system for community-contributed custom actions
- YAML-based configuration with interactive configurator
- Platform support: macOS, Windows, Linux
- CLI flags: --slap-only, --trackpad-only, --slap-method, --slap-sensitivity, --escalation
- 30 unit tests covering core, config, and slap modules
- GitHub Actions CI across 3 platforms and Python 3.9-3.12
