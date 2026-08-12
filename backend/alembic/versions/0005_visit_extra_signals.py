"""add country_code, hostname (reverse DNS), and is_mobile to visits/ip_intelligence

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("visits", "ip_intelligence"):
        op.add_column(table, sa.Column("country_code", sa.String(2), nullable=True))
        op.add_column(table, sa.Column("hostname", sa.String(255), nullable=True))
        op.add_column(table, sa.Column("is_mobile", sa.Boolean, nullable=True))


def downgrade() -> None:
    for table in ("visits", "ip_intelligence"):
        op.drop_column(table, "is_mobile")
        op.drop_column(table, "hostname")
        op.drop_column(table, "country_code")
