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
    # db.create_all() przy starcie aplikacji tworzy tabele z modeli, wiec na
    # bazie ktora juz raz wstala ta tabela istnieje, mimo ze alembic o niej
    # "nie wie". Bez tego warunku upgrade wywala sie na 1050 Table already exists.
    if sa.inspect(op.get_bind()).has_table('lead_component'):
        return

    op.create_table('lead_component',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('is_ordered', sa.Boolean(), nullable=False, server_default='0'),
    sa.Column('lead_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['lead_id'], ['lead_main.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    if not sa.inspect(op.get_bind()).has_table('lead_component'):
        return

    op.drop_table('lead_component')
