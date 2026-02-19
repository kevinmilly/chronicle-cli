# Chronicle Telegram Bot

Capture journal entries from your phone via Telegram and sync them to your Chronicle CLI.

## How It Works

1. Send a text message to your bot on Telegram
2. The bot formats it as a Chronicle entry (`@entry/@end` format)
3. Encrypts with Fernet (same passphrase + salt as your CLI)
4. Appends the encrypted token to your GitHub Gist
5. Run `chronicle pull` on your laptop to sync

## Setup

### 1. Create a Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the bot token

### 2. Get Your Telegram User ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your numeric user ID

### 3. Set Up Chronicle Sync

On your laptop, run:
```bash
chronicle sync setup
```
This creates the Gist and generates the encryption salt. Note the Gist ID and salt from your `~/.chronicle/config.toml`.

### 4. Configure the Bot

Copy `.env.example` to `.env` and fill in the values:
```bash
cp .env.example .env
```

The `CHRONICLE_SYNC_SALT` must match the `encryption_salt` from your Chronicle config.

### 5. Install & Run

```bash
pip install -r requirements.txt
python bot.py
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/tag work,python` | Set tags for the next entry |
| `/people Alice,Bob` | Set people for the next entry |
| `/type decision` | Set entry type (default: `entry`) |
| `/status` | Show bot status |

Any plain text message becomes a journal entry.

## Deployment Options

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

### Free-tier hosting
- **Railway** — connect your repo, set env vars, deploy
- **Render** — background worker, set env vars
- **Oracle Cloud** — always-free ARM instance

### Serverless (webhook mode)
For Lambda/Cloud Functions, switch from polling to webhook mode in `bot.py`. See the [python-telegram-bot wiki](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks) for details.

## Security

- Only messages from `CHRONICLE_AUTHORIZED_USER_ID` are processed
- All entries are encrypted before upload (Fernet + PBKDF2)
- The Gist is "secret" (unlisted) — not discoverable but not truly private
- The passphrase is never stored on disk in the CLI (prompted or env var)
