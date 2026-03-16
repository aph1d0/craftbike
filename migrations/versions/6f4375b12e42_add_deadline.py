"""add deadline

Revision ID: 6f4375b12e42
Revises: 678b33cdd2b9
Create Date: 2026-03-16 09:45:57.821930

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '6f4375b12e42'
down_revision = '678b33cdd2b9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('lead_main', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deadline', sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table('lead_main', schema=None) as batch_op:
        batch_op.drop_column('deadline')
