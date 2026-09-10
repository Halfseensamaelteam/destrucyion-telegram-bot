# Termux Development Guide

This document outlines how to set up and run `destrucyion-telegram-bot` locally on Android using Termux.

## Prerequisites

1. Install [Termux](https://f-droid.org/en/packages/com.termux/) from F-Droid (do not use the Google Play Store version as it is deprecated).
2. Update the package manager:
   ```bash
   pkg update && pkg upgrade -y
   ```

## 1. Install System Dependencies

The project requires Python, Git, build tools (Clang, Rust, Make, pkg-config) for compiling native packages (`cryptography`, `asyncpg`, `pydantic-core` if ARM wheels are unavailable), and optionally PostgreSQL:

```bash
pkg install -y python rust clang make pkg-config git postgresql libffi openssl
```

## 2. Install uv

Install `uv` package manager via `pip` on Termux:

```bash
pip install uv
```

## 3. Clone Repository and Setup

```bash
git clone https://github.com/cahsun147/destrucyion-telegram-bot.git
cd destrucyion-telegram-bot

# Copy environment template
cp .env.example .env
```

Generate your session encryption key:
```bash
python scripts/generate_key.py
```
Copy the generated key, open `.env`, and fill in your values:
```bash
nano .env
```

## 4. Install Project Packages

```bash
uv sync --extra dev
```

> **Note on PostgreSQL vs SQLite**:
> The production architecture uses PostgreSQL (`asyncpg`). PostgreSQL can run natively inside Termux (initialized via `initdb` and started via `pg_ctl`), or you can point `DATABASE_URL` in `.env` to a remote Postgres instance (e.g. Supabase/Neon).

## 5. Verify & Run the Application

Run the tests to verify the installation:
```bash
uv run pytest
```

Start the components:

**Terminal 1 (FastAPI App):**
```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 (Worker Supervisor):**
```bash
uv run python -m worker.main
```

## Known Tips & Workarounds on Termux

- **Android Battery Optimization**: Disable battery optimization / enable "Acquire Wakelock" inside Termux (`termux-wake-lock`) so Android does not kill the persistent worker in the background.
- **Compilation Speed**: Compiling wheels like `cryptography` or `asyncpg` for Android ARM may take 1–3 minutes on first install. Be patient during `uv sync`.
