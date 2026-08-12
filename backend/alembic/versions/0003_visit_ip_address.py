"""store raw client IP address on visits

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("visits", sa.Column("ip_address", sa.String(45), nullable=True))
    op.create_index("ix_visits_ip_address", "visits", ["ip_address"])


def downgrade() -> None:
    op.drop_index("ix_visits_ip_address", table_name="visits")
    op.drop_column("visits", "ip_address")
