# Contributing to TapCraft

Thanks for your interest in contributing to TapCraft! Whether you're fixing a bug, adding a feature, or sharing a creative plugin, we appreciate your help.

## Ways to Contribute

### 🐛 Report Bugs
Open an issue with:
- Your OS and version
- Python version
- Steps to reproduce
- Expected vs actual behavior
- Console output (run with `--log` flag)

### 🧩 Share Action Plugins
Create awesome plugins and submit a PR to the `plugins/` directory! Some ideas:
- Spotify / Apple Music controls
- Smart home device triggers (Hue lights, etc.)
- Pomodoro timer
- Screenshot and annotate
- Window management (tile, maximize, move)
- AI assistant trigger
- Quick emoji picker

### 🎵 Sound Packs
Create themed sound packs and add them to `sounds/`. Include a `README.md` in your sound pack folder with attribution and license info.

### 🖥️ Platform Support
Help improve trackpad detection on:
- Windows Precision Touchpads
- Linux Wayland sessions
- Specific trackpad hardware

### 📖 Documentation
- Improve the README
- Write tutorials or blog posts
- Create video demos
- Translate docs

## Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/tapcraft.git
cd tapcraft

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in development mode
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v
```

## Pull Request Process

1. Fork the repo and create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Add tests if applicable
4. Run existing tests: `python -m pytest tests/ -v`
5. Update documentation if needed
6. Submit your PR with a clear description

## Code Style

- Python 3.8+ compatible
- Use type hints where practical
- Follow PEP 8 (we're not strict about line length — 100 chars is fine)
- Docstrings for public functions and classes
- Keep platform-specific code in `tapcraft/platforms/`

## Plugin Guidelines

When creating plugins:
- Inherit from `TapPlugin` base class
- Use a unique, descriptive `name` attribute
- Handle errors gracefully (don't crash TapCraft)
- Document the expected `value` format
- Include example config in your plugin's docstring
- Keep external dependencies minimal

## Community Standards

- Be kind and constructive
- Respect different experience levels
- Focus on the idea, not the person
- Help others learn

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
