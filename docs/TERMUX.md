# Termux Development Guide

This document outlines how to set up and run `destrucyion-telegram-bot` on Android using Termux.

> **Why special instructions?**  
> Some dependencies (`cryptography`, `pydantic-core`, `ruff`, `watchfiles`) require compiling from Rust/C source code. On Android ARM64, this can take **30–60 minutes** and may fail. The guide below uses Termux's own pre-compiled packages where possible to avoid this.

---

## Prerequisites

Install [Termux](https://f-droid.org/en/packages/com.termux/) from **F-Droid** (not the Google Play version — it is outdated and unsupported).

---

## 1. Update Package Manager

```bash
pkg update && pkg upgrade -y
```

---

## 2. Install System-level Dependencies via `pkg`

`pkg` provides pre-compiled binaries for Android ARM64. Install heavy packages this way to **avoid long source compilation**:

```bash
# Core runtime + build tools
pkg install -y python git openssl libffi

# Pre-compiled heavy packages (avoids 30-60 min Rust compile)
pkg install -y python-cryptography python-pydantic

# uv package manager (via pkg — faster than pip on Android)
pkg install -y uv
```

> **Note:** Do NOT use `pip install cryptography` or `pip install pydantic-core` — those will trigger source compilation on ARM64 because PyPI has no Android ARM wheels.

---

## 3. Clone Repository

```bash
git clone https://github.com/cahsun147/destrucyion-telegram-bot.git
cd destrucyion-telegram-bot
```

---

## 4. Setup Environment Variables

```bash
cp .env.example .env
```

Generate a session encryption key:
```bash
python scripts/generate_key.py
```

Open `.env` and fill in your values:
```bash
nano .env
```

Required fields in `.env`:
- `SESSION_ENCRYPTION_KEY` — paste the key generated above
- `API_ID`, `API_HASH` — from https://my.telegram.org
- `BOT_TOKEN` — from @BotFather
- `DATABASE_URL` — your PostgreSQL URL or a local SQLite fallback (see note below)

> **SQLite fallback for local dev:** If you don't have a Postgres instance, set:
> ```
> DATABASE_URL=sqlite+aiosqlite:///./dev.db
> ```

---

## 5. Create Virtual Environment with System Site Packages

This allows uv to **reuse** the pre-compiled `cryptography` and `pydantic` from step 2 instead of recompiling them:

```bash
uv venv --system-site-packages .venv
```

---

## 6. Install Project Dependencies (Production only — no dev extras)

```bash
uv sync --no-dev
```

This skips `ruff`, `watchfiles`, and `ast-serialize` (dev/lint tools that require long Rust compilation and are not needed to run the bot).

---

## 7. Verify Installation

```bash
uv run python -c "import cryptography, pydantic, fastapi, telethon; print('All OK')"
```

---

## 8. Run the Application

You need two Termux sessions (or use `tmux`):

**Terminal 1 — FastAPI App:**
```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Worker Supervisor:**
```bash
uv run python -m worker.main
```

---

## Tips for Termux

| Problem | Solution |
|---|---|
| Android kills background worker | Run `termux-wake-lock` before starting the worker |
| `uv sync` compiling for ages | Use `--no-dev` and `--system-site-packages` as above |
| `pip install` fails for native packages | Use `pkg install python-<package>` instead |
| Want multiple terminals | Install `tmux`: `pkg install tmux` |
