"""add_is_deleted_to_orders

Revision ID: bf57d03394fd
Revises: 84670c4f7c18
Create Date: 2025-03-19 02:55:20.994108

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bf57d03394fd'
down_revision: Union[str, None] = '84670c4f7c18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('orders', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))

def downgrade():
    op.drop_column('orders', 'is_deleted')