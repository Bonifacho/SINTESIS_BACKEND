"""add composite B-Tree indexes and unique constraints

Revision ID: d94f1a82e3b0
Revises: c58e92a10d3f
Create Date: 2026-11-08 21:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'd94f1a82e3b0'
down_revision = 'c58e92a10d3f'
branch_labels = None
depends_on = None


INDEXES_TO_CREATE = [
    # Core Security
    ('persons', 'idx_person_email_active', ['email', 'is_active']),
    ('user_has_role', 'idx_uhr_user_active', ['user_id', 'is_active']),
    ('password_reset_tokens', 'idx_prt_user_used_expires', ['user_id', 'is_used', 'expires_at']),
    # Core Academic
    ('academic_groups', 'idx_group_teacher_active', ['teacher_id', 'is_active']),
    ('academic_enrollments', 'idx_enroll_student_group_active', ['student_id', 'group_id', 'is_active']),
    ('academic_enrollments', 'idx_enroll_group_active', ['group_id', 'is_active']),
    ('academic_topics', 'idx_topic_group_active_order', ['group_id', 'is_active', 'order_index']),
    ('academic_ovas', 'idx_ova_topic_active_order', ['topic_id', 'is_active', 'order_index']),
    ('academic_ova_resources', 'idx_resource_ova_active_order', ['ova_id', 'is_active', 'order_index']),
    ('exam_questions', 'idx_question_exam_active_order', ['exam_id', 'is_active', 'order_index']),
    ('exam_options', 'idx_option_question_active_order', ['question_id', 'is_active', 'order_index']),
    ('exam_attempts', 'idx_attempt_student_exam_active', ['student_id', 'exam_id', 'is_active']),
    ('exam_attempts', 'idx_attempt_exam_active_submitted', ['exam_id', 'is_active', 'submitted_at']),
    ('exam_attempts', 'idx_attempt_student_active_submitted', ['student_id', 'is_active', 'submitted_at']),
    ('exam_attempt_answers', 'idx_att_ans_attempt_active', ['attempt_id', 'is_active']),
    ('academic_group_observers', 'idx_observer_user_group_active', ['observer_id', 'group_id', 'is_active']),
    ('student_progress', 'idx_progress_ova_user_created', ['ova_id', 'user_id', 'created_at']),
    ('student_progress', 'idx_progress_user_created', ['user_id', 'created_at']),
]

UNIQUE_CONSTRAINTS_TO_CREATE = [
    ('academic_enrollments', 'uq_enrollment_group_student', ['group_id', 'student_id']),
    ('exam_attempt_answers', 'uq_attempt_question', ['attempt_id', 'question_id']),
]


def _get_existing_names(inspector: Inspector, table_name: str) -> set[str]:
    names = {idx['name'] for idx in inspector.get_indexes(table_name) if idx.get('name')}
    for uq in inspector.get_unique_constraints(table_name):
        if uq.get('name'):
            names.add(uq['name'])
    return names


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # 1. Crear UniqueConstraints (idempotente)
    for table_name, uq_name, columns in UNIQUE_CONSTRAINTS_TO_CREATE:
        existing = _get_existing_names(inspector, table_name)
        if uq_name not in existing:
            op.create_unique_constraint(uq_name, table_name, columns)

    # 2. Crear índices compuestos B-Tree (idempotente)
    for table_name, idx_name, columns in INDEXES_TO_CREATE:
        existing = _get_existing_names(inspector, table_name)
        if idx_name not in existing:
            op.create_index(idx_name, table_name, columns, unique=False)


def downgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    for table_name, idx_name, _ in reversed(INDEXES_TO_CREATE):
        existing = _get_existing_names(inspector, table_name)
        if idx_name in existing:
            op.drop_index(idx_name, table_name=table_name)

    for table_name, uq_name, _ in reversed(UNIQUE_CONSTRAINTS_TO_CREATE):
        existing = _get_existing_names(inspector, table_name)
        if uq_name in existing:
            op.drop_constraint(uq_name, table_name, type_='unique')
