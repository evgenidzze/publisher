"""4

Revision ID: 4494fdfedb7d
Revises: f1ecbd2a4396
Create Date: 2024-05-31 12:25:55.332904

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4494fdfedb7d'
down_revision: Union[str, None] = 'f1ecbd2a4396'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
