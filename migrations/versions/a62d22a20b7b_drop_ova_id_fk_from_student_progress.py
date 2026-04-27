"""drop ova_id FK from student_progress

Revision ID: a62d22a20b7b
Revises: 02be1f08fb4e
Create Date: 2026-04-26 23:16:44.076335

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a62d22a20b7b'
down_revision = '02be1f08fb4e'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('student_progress_ibfk_1', 'student_progress', type_='foreignkey')


def downgrade():
    op.create_foreign_key('student_progress_ibfk_1', 'student_progress',
                          'academic_ovas', ['ova_id'], ['id'])
