"""Initial schema: users, telegram_accounts, subscriptions, media_records.

Revision ID: 0001
Revises: None
Create Date: 2026-09-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # users                                                                #
    # ------------------------------------------------------------------ #
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_telegram_user_id", "users", ["telegram_user_id"], unique=True)

    # ------------------------------------------------------------------ #
    # telegram_accounts                                                    #
    # ------------------------------------------------------------------ #
    op.create_table(
        "telegram_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("phone_masked", sa.String(length=50), nullable=True),
        sa.Column("session_ciphertext", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "paused", "error", "disconnected", name="telegramaccountstatus"),
            nullable=False,
            server_default="disconnected",
        ),
        sa.Column("last_connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_telegram_accounts_user_id", "telegram_accounts", ["user_id"])
    op.create_index("ix_telegram_accounts_telegram_user_id", "telegram_accounts", ["telegram_user_id"])

    # ------------------------------------------------------------------ #
    # subscriptions                                                        #
    # ------------------------------------------------------------------ #
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "plan",
            sa.Enum("weekly", "monthly", "lifetime", name="subscriptionplan"),
            nullable=False,
        ),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "expired", "cancelled", name="subscriptionstatus"),
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"], unique=True)

    # ------------------------------------------------------------------ #
    # media_records                                                        #
    # ------------------------------------------------------------------ #
    op.create_table(
        "media_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("telegram_account_id", sa.Integer(), nullable=False),
        sa.Column("source_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("source_chat_title", sa.String(length=512), nullable=True),
        sa.Column("source_chat_username", sa.String(length=255), nullable=True),
        sa.Column("source_message_id", sa.BigInteger(), nullable=False),
        sa.Column("sender_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("sender_username", sa.String(length=255), nullable=True),
        sa.Column("sender_display_name", sa.String(length=512), nullable=True),
        sa.Column(
            "media_type",
            sa.Enum("photo", "video", "document", "voice", "video_note", "sticker", "unknown", name="mediatype"),
            nullable=False,
        ),
        sa.Column("ttl_seconds", sa.Integer(), nullable=True),
        sa.Column("saved_message_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "saved", "failed", "skipped", name="mediarecordstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["telegram_account_id"], ["telegram_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "telegram_account_id", "source_chat_id", "source_message_id",
            name="uq_media_record_idempotency",
        ),
    )
    op.create_index("ix_media_records_user_id", "media_records", ["user_id"])
    op.create_index("ix_media_records_telegram_account_id", "media_records", ["telegram_account_id"])
    op.create_index("ix_media_records_status", "media_records", ["status"])
    op.create_index("ix_media_records_created_at", "media_records", ["created_at"])


def downgrade() -> None:
    op.drop_table("media_records")
    op.drop_table("subscriptions")
    op.drop_table("telegram_accounts")
    op.drop_table("users")
    # Drop enums explicitly (needed for PostgreSQL)
    sa.Enum(name="mediarecordstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="mediatype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="subscriptionstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="subscriptionplan").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="telegramaccountstatus").drop(op.get_bind(), checkfirst=True)
