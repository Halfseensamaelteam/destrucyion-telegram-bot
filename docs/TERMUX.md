# Termux Development Guide

This document outlines how to set up and run destrucyion-telegram-bot locally on Android using Termux.

## Prerequisites

1. Install [Termux](https://f-droid.org/en/packages/com.termux/) from F-Droid (do not use the Google Play Store version).
2. Update the package manager:
   `ash
   pkg update && pkg upgrade -y
   ``n
## 1. Install Dependencies

The project requires Python, Rust (for cryptography/pydantic compilation if wheels are missing), and basic build tools:

`ash
pkg install -y python rust clang make pkg-config git postgresql
``n
## 2. Install uv`n
Install the uv package manager. On Termux, you can install it via pip:

`ash
pip install uv
``n
## 3. Clone and Setup

`ash
git clone <your-repo-url> destrucyion-telegram-bot
cd destrucyion-telegram-bot

# Create the .env file
cp .env.example .env
``n
Edit the .env file with your credentials:
`ash
nano .env
``n
## 4. Install Project Packages

`ash
uv sync
``n
> **Note on PostgreSQL vs SQLite**:
> The production architecture uses PostgreSQL (syncpg). PostgreSQL can run natively in Termux (started via pg_ctl), but if you encounter compilation issues with syncpg on Android ARM64, you can modify DATABASE_URL in .env to use SQLite for local development (e.g., sqlite+aiosqlite:///./dev.db). The SQLAlchemy configuration (implemented in Phase 3) will handle this fallback.

## 5. Run the Application

**Terminal 1 (FastAPI):**
`ash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
``n
**Terminal 2 (Worker):**
`ash
uv run python -m worker.main
``n
## Known Limitations on Termux
- Cryptography packages might take a while to compile from source on older Android devices.
- Termux might kill background processes if Android's aggressive battery optimization is enabled. Disable battery optimization for Termux if you want the worker to run continuously.
