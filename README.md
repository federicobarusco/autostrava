# Strava Kudos Giver 👍👍👍

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-312/)

A Python tool to automatically give [Strava](https://www.strava.com) Kudos to recent activities on your feed using browser automation.

## 🏃 Usage

### Local Execution

```bash
# Install dependencies
poetry install

# Install Playwright browsers
poetry run playwright install firefox

# Set environment variables
export STRAVA_EMAIL=your_email@example.com
export STRAVA_PASSWORD=your_password
export BASE_URL=https://www.strava.com

# Run the script
poetry run python -m autostrava
```

### Debug Mode

If login is failing, run in debug mode to see the browser:

```bash
export AUTOSTRAVA_DEBUG=1
poetry run python -m autostrava
```

This will open a visible browser window so you can see what's happening during login.

## 🛠️ Setup

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/) for dependency management
- Firefox (installed via Playwright)

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `STRAVA_EMAIL` | Yes | Your Strava login email |
| `STRAVA_PASSWORD` | Yes | Your Strava password |
| `BASE_URL` | No | Strava base URL (default: `https://www.strava.com`) |
| `AUTOSTRAVA_DEBUG` | No | Set to `1` to run with visible browser |

### GitHub Actions

1. Fork the repo
2. Go to Settings → Security → Secrets and Variables → Actions
3. Add `STRAVA_EMAIL` and `STRAVA_PASSWORD` as repository secrets
4. The action runs automatically on schedule

## 🛡️ Anti-Bot Detection

This project uses several techniques to avoid bot detection:

- **Playwright Stealth**: Hides automation signals from the browser
- **Human-like delays**: Random delays between actions (typing, clicking, scrolling)
- **Realistic scrolling**: Variable scroll patterns that mimic human behavior
- **Login verification**: Detects CAPTCHA and login failures with screenshots

### If Login Fails

1. **Run in debug mode** (`AUTOSTRAVA_DEBUG=1`) to see what's happening
2. **Check `login_failed.png`** - A screenshot is saved when login fails
3. **Manual CAPTCHA**: If Strava shows a CAPTCHA, you may need to log in manually once to "trust" your IP
4. **Try from a different IP**: Some IPs may be flagged by Strava's anti-bot systems
5. **Wait and retry**: Strava may temporarily block automated access; try again later

### Known Limitations

- Strava actively detects and blocks automation tools
- CAPTCHA challenges cannot be bypassed automatically
- Running from cloud IPs (like GitHub Actions) may trigger additional verification

## 🔬 Testing

```bash
poetry run pytest
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.
