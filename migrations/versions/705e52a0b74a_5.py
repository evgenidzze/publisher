"""5

Revision ID: 705e52a0b74a
Revises: 4494fdfedb7d
Create Date: 2024-05-31 12:33:26.541813

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '705e52a0b74a'
down_revision: Union[str, None] = '4494fdfedb7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
