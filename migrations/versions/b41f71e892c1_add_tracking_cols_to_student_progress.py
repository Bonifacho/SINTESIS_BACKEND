"""add tracking columns to student_progress

Revision ID: b41f71e892c1
Revises: a69cb354de0c
Create Date: 2026-10-17 01:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'b41f71e892c1'
down_revision = 'a69cb354de0c'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_cols = [c['name'] for c in inspector.get_columns('student_progress')]

    with op.batch_alter_table('student_progress', schema=None) as batch_op:
        if 'topic_name' not in existing_cols:
            batch_op.add_column(sa.Column('topic_name', sa.String(length=150), nullable=True))
        if 'resource_name' not in existing_cols:
            batch_op.add_column(sa.Column('resource_name', sa.String(length=150), nullable=True))


def downgrade():
    with op.batch_alter_table('student_progress', schema=None) as batch_op:
        batch_op.drop_column('resource_name')
        batch_op.drop_column('topic_name')
