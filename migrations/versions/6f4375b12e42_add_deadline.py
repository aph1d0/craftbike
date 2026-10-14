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


def has_deadline_column():
    columns = sa.inspect(op.get_bind()).get_columns('lead_main')
    return any(column['name'] == 'deadline' for column in columns)


def upgrade():
    # patrz komentarz w 678b33cdd2b9: na bazie zalozonej przez db.create_all()
    # kolumna moze juz istniec, zanim alembic do tej rewizji dojdzie
    if has_deadline_column():
        return

    with op.batch_alter_table('lead_main', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deadline', sa.Date(), nullable=True))


def downgrade():
    if not has_deadline_column():
        return

    with op.batch_alter_table('lead_main', schema=None) as batch_op:
        batch_op.drop_column('deadline')
