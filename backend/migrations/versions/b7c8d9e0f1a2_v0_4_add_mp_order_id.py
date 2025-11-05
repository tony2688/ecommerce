"""v0.4 add mp_order_id to payment_intents

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2025-11-04
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c8d9e0f1a2'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('payment_intents', sa.Column('mp_order_id', sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column('payment_intents', 'mp_order_id')