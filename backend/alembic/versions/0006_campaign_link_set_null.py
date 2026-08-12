"""links.campaign_id: ON DELETE CASCADE -> SET NULL

Deleting a campaign should un-link its links, not delete them along with
their entire visit history — that's a surprising, unrecoverable data-loss
trap for something that reads like routine cleanup.

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-08

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("links_campaign_id_fkey", "links", type_="foreignkey")
    op.create_foreign_key(
        "links_campaign_id_fkey", "links", "campaigns", ["campaign_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("links_campaign_id_fkey", "links", type_="foreignkey")
    op.create_foreign_key(
        "links_campaign_id_fkey", "links", "campaigns", ["campaign_id"], ["id"], ondelete="CASCADE"
    )
