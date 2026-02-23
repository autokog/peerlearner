"""add role and audit_log

Revision ID: b3c2d1e4f5a6
Revises: af1187c61db7
Create Date: 2026-02-23 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3c2d1e4f5a6'
down_revision = 'af1187c61db7'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    insp = sa.inspect(conn)

    # Add role column if not already present (idempotent for legacy DBs)
    existing_cols = [c['name'] for c in insp.get_columns('users')]
    if 'role' not in existing_cols:
        op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False, server_default='user'))

    # Create audit_logs only if it doesn't already exist
    if 'audit_logs' not in insp.get_table_names():
        op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )


def downgrade():
    op.drop_table('audit_logs')
    op.drop_column('users', 'role')
