# AGENTS.md

This file follows the common `AGENTS.md` convention so that any AI coding
agent (Antigravity, Claude Code, Cursor, Copilot Workspace, etc.) knows how to
work in this repository.

## Read First

Before making any change, read `CLAUDE.md` in full. It is the primary
specification for this project and takes precedence over general assumptions.

Antigravity users: workspace rules also live in `.agents/rules/project.md`,
which summarizes the same rules for that tool's rules mechanism.

## Project

```
destrucyion-telegram-bot
```

A multi-tenant Telegram service that saves media — especially
timed/self-destructing media — to the *same* connected Telegram account's own
Saved Messages, with per-user subscriptions and an isolated Telethon client
per account.

## Non-Negotiable Rules (summary)

1. **Work in phases.** Follow `docs/ROADMAP.md` in order. Never implement the
   whole system in one pass. Stop and report at every phase gate.
2. **Never run a persistent Telethon listener on Vercel.** Vercel is for
   request-driven components only (FastAPI, bot webhook). Long-running
   Telethon clients belong in a persistent worker.
3. **One Telethon client per Telegram account.** Never share a client or
   session across accounts or users.
4. **Tenant isolation is mandatory.** No application user may ever access
   another user's Telegram session, subscription, media records, or account
   info.
5. **Sessions are credentials.** Never log, expose, commit, or return a
   Telegram session string through any interface. Encrypt at rest.
6. **PostgreSQL is authoritative for subscriptions.** Never use in-memory
   timers or Redis as the source of truth.
7. **Idempotency is database-enforced**, keyed on
   `telegram_account_id + source_chat_id + source_message_id`. Never use a
   Python `set()` for this.
8. **Don't over-promise.** Never claim every self-destructing media item can
   always be captured — report actual success/failure.

## Commands

_Fill in once Phase 1 establishes the real tooling:_

```bash
# install
uv sync

# run tests
pytest

# run API
uvicorn app.main:app --reload

# run worker
python -m worker.main

# migrations
alembic upgrade head
```

## Where Things Live

- `CLAUDE.md` — full specification (read this first).
- `docs/ROADMAP.md` — phase-by-phase implementation plan.
- `docs/ARCHITECTURE.md` — system architecture and diagrams.
- `docs/DEVELOPMENT.md` — local setup (Docker and Termux).
- `docs/INITIAL-AUDIT.md` — Phase 0 deliverable (audit of the original repo).
- `docs/TERMUX.md` — Phase 2 deliverable (verified Termux setup).
- `.agents/rules/project.md` — condensed rules for Antigravity's rules system.
