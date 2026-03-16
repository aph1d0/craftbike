"""add components

Revision ID: 678b33cdd2b9
Revises: 56a0ecfd603a
Create Date: 2026-03-15 20:58:15.897950

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '678b33cdd2b9'
down_revision = '56a0ecfd603a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('lead_component',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('is_ordered', sa.Boolean(), nullable=False, server_default='0'),
    sa.Column('lead_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['lead_id'], ['lead_main.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('lead_component')
