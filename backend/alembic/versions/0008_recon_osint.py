"""recon/osint: extend security_scans with subdomains, ip_info, dns_propagation, cookie_info, tech_info, robots_info, findings

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_COLUMNS = ["ip_info", "subdomains", "dns_propagation", "cookie_info", "tech_info", "robots_info", "findings"]


def upgrade() -> None:
    for column in _NEW_COLUMNS:
        op.add_column("security_scans", sa.Column(column, postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    for column in _NEW_COLUMNS:
        op.drop_column("security_scans", column)
