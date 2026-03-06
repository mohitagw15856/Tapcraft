# Security Policy

## Important Notes

TapCraft interacts with system-level input devices and can execute shell commands. Please be aware:

- **Accelerometer mode requires sudo/root access** on macOS. Only run TapCraft from trusted sources.
- **The `command` action type executes arbitrary shell commands.** Be careful with configs from untrusted sources.
- **The `script` action type runs Python files.** Only use plugins you trust.
- Never run a `config.yaml` from an untrusted source without reviewing it first.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT open a public GitHub issue.**
2. Email the maintainers directly (see repo profile) with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
3. We will acknowledge receipt within 48 hours and work on a fix.

Thank you for helping keep TapCraft safe!
