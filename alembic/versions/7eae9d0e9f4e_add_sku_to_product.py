"""Add sku to Product

Revision ID: 7eae9d0e9f4e
Revises: 049094ec1dce
Create Date: 2025-03-06 00:30:24.429964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7eae9d0e9f4e'
down_revision: Union[str, None] = '049094ec1dce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('products', sa.Column('sku', sa.String(), nullable=False))
    op.create_unique_constraint(None, 'products', ['sku'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'products', type_='unique')
    op.drop_column('products', 'sku')
    # ### end Alembic commands ###
