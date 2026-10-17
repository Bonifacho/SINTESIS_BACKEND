"""add snapshot columns to exam_attempts (BE-03)

Revision ID: c58e92a10d3f
Revises: b41f71e892c1
Create Date: 2026-10-17 01:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'c58e92a10d3f'
down_revision = 'b41f71e892c1'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_cols = [c['name'] for c in inspector.get_columns('exam_attempts')]

    with op.batch_alter_table('exam_attempts', schema=None) as batch_op:
        if 'score' not in existing_cols:
            batch_op.add_column(sa.Column('score', sa.Integer(), nullable=True))
        if 'passed' not in existing_cols:
            batch_op.add_column(sa.Column('passed', sa.Boolean(), nullable=True))
        if 'total_questions' not in existing_cols:
            batch_op.add_column(sa.Column('total_questions', sa.Integer(), nullable=True))
        if 'total_points' not in existing_cols:
            batch_op.add_column(sa.Column('total_points', sa.Integer(), nullable=True))
        if 'earned_points' not in existing_cols:
            batch_op.add_column(sa.Column('earned_points', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('exam_attempts', schema=None) as batch_op:
        batch_op.drop_column('earned_points')
        batch_op.drop_column('total_points')
        batch_op.drop_column('total_questions')
        batch_op.drop_column('passed')
        batch_op.drop_column('score')
