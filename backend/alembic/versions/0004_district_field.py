"""add district (neighborhood-level location) to visits and ip_intelligence

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("visits", sa.Column("district", sa.String(100), nullable=True))
    op.add_column("ip_intelligence", sa.Column("district", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("ip_intelligence", "district")
    op.drop_column("visits", "district")
