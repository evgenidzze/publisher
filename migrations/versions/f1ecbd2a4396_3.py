"""3

Revision ID: f1ecbd2a4396
Revises: ed11dab06831
Create Date: 2024-05-30 15:27:25.929223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1ecbd2a4396'
down_revision: Union[str, None] = 'ed11dab06831'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
