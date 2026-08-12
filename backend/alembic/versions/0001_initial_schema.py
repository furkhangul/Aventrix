"""initial schema: users, sessions, campaigns, links, visits, ip_intelligence, audit_logs

Revision ID: 0001
Revises:
Create Date: 2026-08-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="USER"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("email_verification_token_hash", sa.String(255), nullable=True),
        sa.Column("email_verification_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_reset_token_hash", sa.String(255), nullable=True),
        sa.Column("password_reset_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_2fa_enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("totp_secret", sa.String(64), nullable=True),
        sa.Column("backup_codes_hashed", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])

    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.String(2000), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_campaigns_user_id", "campaigns", ["user_id"])

    op.create_table(
        "links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=True),
        sa.Column("short_code", sa.String(64), nullable=False, unique=True),
        sa.Column("target_url", sa.String(2048), nullable=False),
        sa.Column("description", sa.String(2000), nullable=True),
        sa.Column("tags", postgresql.JSONB, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_password_protected", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("requires_consent", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("utm_params", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_links_user_id", "links", ["user_id"])
    op.create_index("ix_links_campaign_id", "links", ["campaign_id"])
    op.create_index("ix_links_short_code", "links", ["short_code"], unique=True)

    op.create_table(
        "visits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("link_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("links.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True),
        sa.Column("consent_given", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("visitor_hash", sa.String(64), nullable=True),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("isp", sa.String(255), nullable=True),
        sa.Column("asn", sa.String(32), nullable=True),
        sa.Column("organization", sa.String(255), nullable=True),
        sa.Column("is_vpn", sa.String(10), nullable=False, server_default="UNKNOWN"),
        sa.Column("is_proxy", sa.String(10), nullable=False, server_default="UNKNOWN"),
        sa.Column("is_tor", sa.String(10), nullable=False, server_default="UNKNOWN"),
        sa.Column("is_hosting", sa.String(10), nullable=False, server_default="UNKNOWN"),
        sa.Column("browser", sa.String(100), nullable=True),
        sa.Column("browser_version", sa.String(50), nullable=True),
        sa.Column("os", sa.String(100), nullable=True),
        sa.Column("os_version", sa.String(50), nullable=True),
        sa.Column("device_type", sa.String(50), nullable=True),
        sa.Column("language", sa.String(20), nullable=True),
        sa.Column("referrer", sa.String(2048), nullable=True),
        sa.Column("bot_confidence", sa.String(20), nullable=False, server_default="UNKNOWN"),
        sa.Column("utm_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_visits_link_id", "visits", ["link_id"])
    op.create_index("ix_visits_campaign_id", "visits", ["campaign_id"])
    op.create_index("ix_visits_created_at", "visits", ["created_at"])
    op.create_index("ix_visits_ip_hash", "visits", ["ip_hash"])
    op.create_index("ix_visits_visitor_hash", "visits", ["visitor_hash"])

    op.create_table(
        "ip_intelligence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ip_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=True),
        sa.Column("latitude", sa.Float, nullable=True),
        sa.Column("longitude", sa.Float, nullable=True),
        sa.Column("isp", sa.String(255), nullable=True),
        sa.Column("asn", sa.String(32), nullable=True),
        sa.Column("organization", sa.String(255), nullable=True),
        sa.Column("is_vpn", sa.String(10), nullable=False, server_default="UNKNOWN"),
        sa.Column("is_proxy", sa.String(10), nullable=False, server_default="UNKNOWN"),
        sa.Column("is_tor", sa.String(10), nullable=False, server_default="UNKNOWN"),
        sa.Column("is_hosting", sa.String(10), nullable=False, server_default="UNKNOWN"),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ip_intelligence_ip_hash", "ip_intelligence", ["ip_hash"], unique=True)

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_email_snapshot", sa.String(320), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(64), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("result", sa.String(10), nullable=False),
        sa.Column("log_metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("ip_intelligence")
    op.drop_table("visits")
    op.drop_table("links")
    op.drop_table("campaigns")
    op.drop_table("sessions")
    op.drop_table("users")
