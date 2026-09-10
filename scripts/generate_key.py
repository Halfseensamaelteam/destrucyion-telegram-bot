#!/usr/bin/env python3
"""
Generate a Fernet encryption key for SESSION_ENCRYPTION_KEY.

Usage:
    python scripts/generate_key.py

Copy the output into your .env file as SESSION_ENCRYPTION_KEY=<value>.
"""

from cryptography.fernet import Fernet

key = Fernet.generate_key().decode()
print(f"SESSION_ENCRYPTION_KEY={key}")
