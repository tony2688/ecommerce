"""v0.4 add order addresses FKs and snapshots, extend status enum

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2025-11-04
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2e3f4a5b6c7'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add FK columns for selected addresses
    op.add_column('orders', sa.Column('shipping_address_id', sa.Integer(), nullable=True))
    op.add_column('orders', sa.Column('billing_address_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_orders_shipping_address', 'orders', 'addresses', ['shipping_address_id'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_orders_billing_address', 'orders', 'addresses', ['billing_address_id'], ['id'], ondelete='SET NULL'
    )
    op.create_index('ix_orders_shipping_address_id', 'orders', ['shipping_address_id'], unique=False)
    op.create_index('ix_orders_billing_address_id', 'orders', ['billing_address_id'], unique=False)

    # Add snapshots JSON columns
    op.add_column('orders', sa.Column('shipping_address_snapshot', sa.JSON(), nullable=True))
    op.add_column('orders', sa.Column('billing_address_snapshot', sa.JSON(), nullable=True))

    # Extend ENUM for order status to include 'addresses_selected'
    # MySQL ENUM alteration
    op.execute(
        "ALTER TABLE orders MODIFY COLUMN status ENUM('pending','addresses_selected','paid','cancelled','expired') NOT NULL DEFAULT 'pending'"
    )


def downgrade() -> None:
    # Revert ENUM
    op.execute(
        "ALTER TABLE orders MODIFY COLUMN status ENUM('pending','paid','cancelled','expired') NOT NULL DEFAULT 'pending'"
    )

    # Drop snapshots
    op.drop_column('orders', 'billing_address_snapshot')
    op.drop_column('orders', 'shipping_address_snapshot')

    # Drop FKs and columns
    op.drop_index('ix_orders_billing_address_id', table_name='orders')
    op.drop_index('ix_orders_shipping_address_id', table_name='orders')
    op.drop_constraint('fk_orders_billing_address', 'orders', type_='foreignkey')
    op.drop_constraint('fk_orders_shipping_address', 'orders', type_='foreignkey')
    op.drop_column('orders', 'billing_address_id')
    op.drop_column('orders', 'shipping_address_id')