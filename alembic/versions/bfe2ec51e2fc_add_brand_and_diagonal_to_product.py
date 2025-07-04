"""add brand and diagonal to Product

Revision ID: bfe2ec51e2fc
Revises: 0564ee14e1ae
Create Date: 2025-03-21 17:17:09.007064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfe2ec51e2fc'
down_revision: Union[str, None] = '0564ee14e1ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###

    # Drop the foreign key constraints that depend on the user_id index first
    op.drop_constraint('fk_orders_user_id', 'orders', type_='foreignkey')
    op.drop_constraint('fk_cart_items_user_id', 'cart_items', type_='foreignkey')

    # Drop the old unique constraints on user_id in the users table
    op.drop_constraint('users_user_id_key', 'users', type_='unique')
    op.drop_constraint('users_user_id_unique', 'users', type_='unique')

    # Alter the column to make sure it's BIGINT
    op.alter_column('users', 'user_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)

    # Create the new foreign key constraints for users table (self-referencing)
    op.create_foreign_key(None, 'users', 'users', ['user_id'], ['user_id'])

    # Re-create the foreign key constraints for orders and cart_items tables
    op.create_foreign_key('fk_cart_items_user_id', 'cart_items', 'users', ['user_id'], ['user_id'])
    op.create_foreign_key('fk_orders_user_id', 'orders', 'users', ['user_id'], ['user_id'])

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###

    # Drop the newly created foreign key constraints
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_constraint(None, 'cart_items', type_='foreignkey')

    # Recreate the old unique constraints on user_id in the users table
    op.create_unique_constraint('users_user_id_unique', 'users', ['user_id'])
    op.create_unique_constraint('users_user_id_key', 'users', ['user_id'])

    # Ensure user_id column in users table stays BIGINT
    op.alter_column('users', 'user_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.BIGINT(),
                    existing_nullable=False)

    # Recreate the old foreign key constraint for the cart_items table
    op.create_foreign_key('fk_cart_items_user_id', 'cart_items', 'users', ['user_id'], ['user_id'])

    # Revert the user_id column type change in cart_items
    op.alter_column('cart_items', 'user_id',
                    existing_type=sa.BIGINT(),
                    type_=sa.BIGINT(),
                    existing_nullable=True)
    # ### end Alembic commands ###
