"""add lead statuses: Wycenione, Pożyczone, Dłużnicy

Revision ID: a1b2c3d4e5f6
Revises: 6f4375b12e42
Create Date: 2026-10-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '6f4375b12e42'
branch_labels = None
depends_on = None


NEW_STATUSES = [
    (9, 'Wycenione'),
    (10, 'Pożyczone'),
    (11, 'Dłużnicy'),
]

lead_status = sa.table(
    'lead_status',
    sa.column('id', sa.Integer),
    sa.column('status_name', sa.String),
    sa.column('is_final', sa.Boolean),
)


def upgrade():
    conn = op.get_bind()
    existing = {
        name for (name,) in conn.execute(sa.select(lead_status.c.status_name)).fetchall()
    }
    rows = [
        {'id': status_id, 'status_name': name, 'is_final': False}
        for status_id, name in NEW_STATUSES
        if name not in existing
    ]
    if rows:
        op.bulk_insert(lead_status, rows)


def downgrade():
    conn = op.get_bind()
    conn.execute(
        lead_status.delete().where(
            lead_status.c.status_name.in_([name for _, name in NEW_STATUSES])
        )
    )
