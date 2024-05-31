"""2

Revision ID: ed11dab06831
Revises: 0d9ede5f4f3f
Create Date: 2024-05-30 13:34:57.174350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed11dab06831'
down_revision: Union[str, None] = '0d9ede5f4f3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
