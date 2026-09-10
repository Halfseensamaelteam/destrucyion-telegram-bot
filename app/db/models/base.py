"""
app.db.models.base
~~~~~~~~~~~~~~~~~~
Shared declarative base for all SQLAlchemy ORM models.
All models must inherit from this Base so Alembic can auto-detect them.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Single declarative base for the entire application."""
    pass
