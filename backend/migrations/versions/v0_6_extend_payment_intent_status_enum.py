from alembic import op


# revision identifiers, used by Alembic.
revision = "f6e7d8c9b0a1"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extender ENUM de payment_intents.status para incluir 'in_process'
    op.execute(
        """
        ALTER TABLE payment_intents 
        MODIFY COLUMN status ENUM('created','approved','rejected','cancelled','expired','in_process') 
        NOT NULL DEFAULT 'created'
        """
    )


def downgrade() -> None:
    # Revertir ENUM a valores originales
    op.execute(
        """
        ALTER TABLE payment_intents 
        MODIFY COLUMN status ENUM('created','approved','rejected','cancelled','expired') 
        NOT NULL DEFAULT 'created'
        """
    )