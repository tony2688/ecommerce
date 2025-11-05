"""v0.4 create addresses table

Revision ID: c1d2e3f4a5b6
Revises: b7c8d9e0f1a2
Create Date: 2025-11-04
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'b7c8d9e0f1a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'addresses',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('kind', sa.Enum('shipping', 'billing', name='address_kind_enum'), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('street', sa.String(length=200), nullable=False),
        sa.Column('city', sa.String(length=120), nullable=False),
        sa.Column('province', sa.String(length=120), nullable=False),
        sa.Column('zip_code', sa.String(length=16), nullable=False),
        sa.Column('country', sa.String(length=2), nullable=False, server_default='AR'),
        sa.Column('phone', sa.String(length=24), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_addresses_user_id', 'addresses', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_addresses_user_id', table_name='addresses')
    op.drop_table('addresses')