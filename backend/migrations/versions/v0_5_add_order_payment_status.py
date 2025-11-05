from alembic import op


# revision identifiers, used by Alembic.
revision = "e4f5a6b7c8d9"
down_revision = "d2e3f4a5b6c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Crear ENUM y columna payment_status en orders
    op.execute(
        """
        ALTER TABLE orders 
        ADD COLUMN payment_status ENUM('pending','approved','rejected','cancelled','expired','in_process') 
        NOT NULL DEFAULT 'pending'
        """
    )
    op.execute("CREATE INDEX ix_orders_payment_status ON orders (payment_status)")


def downgrade() -> None:
    op.execute("DROP INDEX ix_orders_payment_status ON orders")
    op.execute("ALTER TABLE orders DROP COLUMN payment_status")