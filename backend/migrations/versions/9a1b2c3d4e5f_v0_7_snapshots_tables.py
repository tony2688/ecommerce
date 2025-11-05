"""v0.7 snapshots tables

Revision ID: 9a1b2c3d4e5f
Revises: 7f509f60761d
Create Date: 2025-11-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a1b2c3d4e5f'
down_revision: Union[str, None] = '7f509f60761d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'daily_sales',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('orders_paid', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('orders_cancelled', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('revenue_paid', sa.Numeric(12, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('avg_order_value', sa.Numeric(12, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('date', name='uq_daily_sales_date'),
    )

    op.create_table(
        'daily_category_sales',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('category_name', sa.String(length=160), nullable=False),
        sa.Column('revenue_paid', sa.Numeric(12, 2), nullable=False, server_default=sa.text('0')),
        sa.Column('orders_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('date', 'category_id', name='uq_daily_category_sales_date_cat'),
    )


def downgrade() -> None:
    op.drop_table('daily_category_sales')
    op.drop_table('daily_sales')