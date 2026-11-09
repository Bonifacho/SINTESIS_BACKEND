# app/core_academic/repositories.py
from sqlalchemy import text, bindparam, Integer
from app.extensions import db
from app.utils.database import persist_entity
from app.core_academic.models import (
    Group, Enrollment, Topic,
    OVA, OVAResource,
    Exam, Question, Option, AnswerKey,
    ExamAttempt, AttemptAnswer,
    GroupObserver, StudentProgress
)


class AcademicRepository:

    # ── GRUPOS ────────────────────────────────────────────────────────────────
    @staticmethod
    def create_group(group: Group, commit: bool = True) -> Group:
        return persist_entity(group, commit=commit)

    @staticmethod
    def get_group_by_id(group_id: int) -> Group:
        return db.session.query(Group).filter_by(id=group_id).first()

    @staticmethod
    def get_group_by_id_for_update(group_id: int) -> Group:
        """Obtiene el grupo aplicando bloqueo pesimista SELECT ... FOR UPDATE."""
        return (
            db.session.query(Group)
            .filter_by(id=int(group_id))
            .with_for_update()
            .first()
        )

    @staticmethod
    def get_all_groups():
        return db.session.query(Group).filter_by(is_active=True).all()

    # ── MATRÍCULAS ────────────────────────────────────────────────────────────
    @staticmethod
    def create_enrollment(enrollment: Enrollment, commit: bool = True) -> Enrollment:
        return persist_entity(enrollment, commit=commit)

    @staticmethod
    def get_enrollment_by_id(enrollment_id: int) -> Enrollment:
        return db.session.query(Enrollment).filter_by(id=enrollment_id).first()

    @staticmethod
    def get_enrollments_by_group(group_id: int):
        return db.session.query(Enrollment).filter_by(
            group_id=group_id, is_active=True
        ).all()

    @staticmethod
    def get_enrollments_with_students_by_group(group_id: int) -> list[dict]:
        """Consulta SARGable y explícitamente parametrizada que reemplaza el bucle 2N+1 en get_enrollments_by_group."""
        stmt = text("""
            SELECT
                e.id AS id,
                e.student_id AS student_id,
                e.group_id AS group_id,
                e.enrolled_at AS enrolled_at,
                e.is_active AS is_active,
                u.id AS user_exists_id,
                u.username AS username,
                p.first_name AS first_name,
                p.last_name AS last_name
            FROM academic_enrollments e
            LEFT JOIN users u ON u.id = e.student_id
            LEFT JOIN persons p ON p.id = u.person_id
            WHERE e.group_id = :group_id
              AND e.is_active = :active_flag
            ORDER BY e.id ASC
        """).bindparams(
            bindparam("group_id", value=int(group_id), type_=Integer),
            bindparam("active_flag", value=1, type_=Integer),
        )
        rows = db.session.execute(stmt).mappings().all()
        result = []
        for r in rows:
            if r["user_exists_id"] is not None:
                if r["first_name"] is not None or r["last_name"] is not None:
                    full_name = f"{r['first_name'] or ''} {r['last_name'] or ''}"
                else:
                    full_name = ""
                username = r["username"]
            else:
                full_name = "Usuario Eliminado"
                username = "eliminado"

            enrolled_at_val = r["enrolled_at"]
            enrolled_iso = (
                enrolled_at_val.isoformat()
                if hasattr(enrolled_at_val, "isoformat")
                else str(enrolled_at_val) if enrolled_at_val else None
            )
            result.append({
                "id": r["id"],
                "student_id": r["student_id"],
                "full_name": full_name,
                "username": username,
                "group_id": r["group_id"],
                "enrolled_at": enrolled_iso,
                "is_active": bool(r["is_active"]),
            })
        return result

    @staticmethod
    def get_enrollment_by_student_and_group(student_id: int, group_id: int):
        return db.session.query(Enrollment).filter_by(
            student_id=student_id, group_id=group_id, is_active=True
        ).first()

    @staticmethod
    def get_enrollment_by_student_and_group_any(student_id: int, group_id: int):
        """Busca matrícula incluyendo registros inactivos (soft-delete)."""
        return db.session.query(Enrollment).filter_by(
            student_id=student_id, group_id=group_id
        ).first()

    # ── TEMAS ─────────────────────────────────────────────────────────────────
    @staticmethod
    def create_topic(topic: Topic, commit: bool = True) -> Topic:
        return persist_entity(topic, commit=commit)

    @staticmethod
    def get_topic_by_id(topic_id: int) -> Topic:
        return db.session.query(Topic).filter_by(id=topic_id).first()

    # ── OVAs ──────────────────────────────────────────────────────────────────
    @staticmethod
    def create_ova(ova: OVA, commit: bool = True) -> OVA:
        return persist_entity(ova, commit=commit)

    @staticmethod
    def get_ova_by_id(ova_id: int) -> OVA:
        return db.session.query(OVA).filter_by(id=ova_id).first()

    @staticmethod
    def get_ovas_by_topic(topic_id: int):
        return db.session.query(OVA).filter_by(
            topic_id=topic_id, is_active=True
        ).order_by(OVA.order_index).all()

    # ── RECURSOS DE OVA ───────────────────────────────────────────────────────
    @staticmethod
    def create_resource(resource: OVAResource, commit: bool = True) -> OVAResource:
        return persist_entity(resource, commit=commit)

    @staticmethod
    def get_resource_by_id(resource_id: int) -> OVAResource:
        return db.session.query(OVAResource).filter_by(id=resource_id).first()

    @staticmethod
    def get_resources_by_ova(ova_id: int):
        return db.session.query(OVAResource).filter_by(
            ova_id=ova_id, is_active=True
        ).order_by(OVAResource.order_index).all()

    @staticmethod
    def get_resources_by_ovas(ova_ids: list[int]) -> dict[int, list[OVAResource]]:
        """Carga en lote los recursos activos de múltiples OVAs en una sola consulta SARGable."""
        if not ova_ids:
            return {}
        rows = (
            db.session.query(OVAResource)
            .filter(OVAResource.ova_id.in_(ova_ids), OVAResource.is_active == True)
            .order_by(OVAResource.order_index)
            .all()
        )
        grouped: dict[int, list[OVAResource]] = {}
        for r in rows:
            grouped.setdefault(r.ova_id, []).append(r)
        return grouped

    # ── EXÁMENES ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_exam(exam: Exam, commit: bool = True) -> Exam:
        return persist_entity(exam, commit=commit)

    @staticmethod
    def get_exam_by_id(exam_id: int) -> Exam:
        return db.session.query(Exam).filter_by(id=exam_id).first()

    @staticmethod
    def get_exam_by_id_for_update(exam_id: int) -> Exam:
        """Obtiene el examen aplicando bloqueo pesimista SELECT ... FOR UPDATE (control de cupo concurrente)."""
        return (
            db.session.query(Exam)
            .filter_by(id=int(exam_id))
            .with_for_update()
            .first()
        )

    @staticmethod
    def get_exam_by_ova(ova_id: int) -> Exam:
        return db.session.query(Exam).filter_by(
            ova_id=ova_id, is_active=True
        ).first()

    @staticmethod
    def get_exams_by_ovas(ova_ids: list[int]) -> dict[int, Exam]:
        """Carga en lote los exámenes activos de múltiples OVAs en una sola consulta."""
        if not ova_ids:
            return {}
        rows = (
            db.session.query(Exam)
            .filter(Exam.ova_id.in_(ova_ids), Exam.is_active == True)
            .all()
        )
        return {e.ova_id: e for e in rows}

    @staticmethod
    def get_exam_by_ova_any(ova_id: int) -> Exam:
        """Busca examen asociado a un OVA incluyendo registros inactivos (soft-delete)."""
        return db.session.query(Exam).filter_by(
            ova_id=ova_id
        ).first()

    # ── PREGUNTAS ─────────────────────────────────────────────────────────────
    @staticmethod
    def create_question(question: Question, commit: bool = True) -> Question:
        return persist_entity(question, commit=commit)

    @staticmethod
    def get_question_by_id(question_id: int) -> Question:
        return db.session.query(Question).filter_by(id=question_id).first()

    @staticmethod
    def get_questions_by_exam(exam_id: int):
        return db.session.query(Question).filter_by(
            exam_id=exam_id, is_active=True
        ).order_by(Question.order_index).all()

    # ── OPCIONES ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_option(option: Option, commit: bool = True) -> Option:
        return persist_entity(option, commit=commit)

    @staticmethod
    def get_option_by_id(option_id: int) -> Option:
        return db.session.query(Option).filter_by(id=option_id).first()

    @staticmethod
    def get_options_by_question(question_id: int):
        return db.session.query(Option).filter_by(
            question_id=question_id, is_active=True
        ).order_by(Option.order_index).all()

    @staticmethod
    def get_options_by_questions(question_ids: list[int]) -> dict[int, list[Option]]:
        """Carga en lote todas las opciones activas para un conjunto de preguntas (elimina N+1)."""
        if not question_ids:
            return {}
        rows = (
            db.session.query(Option)
            .filter(Option.question_id.in_(question_ids), Option.is_active == True)
            .order_by(Option.order_index)
            .all()
        )
        grouped: dict[int, list[Option]] = {}
        for o in rows:
            grouped.setdefault(o.question_id, []).append(o)
        return grouped

    # ── CLAVE DE RESPUESTAS ───────────────────────────────────────────────────
    @staticmethod
    def create_answer_key(answer_key: AnswerKey, commit: bool = True) -> AnswerKey:
        return persist_entity(answer_key, commit=commit)

    @staticmethod
    def get_answer_key_by_question(question_id: int) -> AnswerKey:
        return db.session.query(AnswerKey).filter_by(
            question_id=question_id, is_active=True
        ).first()

    @staticmethod
    def get_answer_key_by_question_any(question_id: int) -> AnswerKey:
        """Busca clave de respuesta por pregunta incluyendo registros inactivos (soft-delete)."""
        return db.session.query(AnswerKey).filter_by(
            question_id=question_id
        ).first()

    @staticmethod
    def get_answer_keys_by_exam(exam_id: int):
        return (
            db.session.query(AnswerKey)
            .join(Question, AnswerKey.question_id == Question.id)
            .filter(Question.exam_id == exam_id, Question.is_active == True)
            .all()
        )

    # ── INTENTOS ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_attempt(attempt: ExamAttempt, commit: bool = True) -> ExamAttempt:
        return persist_entity(attempt, commit=commit)

    @staticmethod
    def get_attempt_by_id(attempt_id: int) -> ExamAttempt:
        return db.session.query(ExamAttempt).filter_by(id=attempt_id).first()

    @staticmethod
    def get_attempt_by_id_for_update(attempt_id: int) -> ExamAttempt:
        """Obtiene el intento aplicando bloqueo pesimista SELECT ... FOR UPDATE (evita doble envío concurrente)."""
        return (
            db.session.query(ExamAttempt)
            .filter_by(id=int(attempt_id))
            .with_for_update()
            .first()
        )

    @staticmethod
    def get_attempts_by_student_and_exam(student_id: int, exam_id: int):
        return db.session.query(ExamAttempt).filter_by(
            student_id=student_id, exam_id=exam_id, is_active=True
        ).all()

    @staticmethod
    def count_attempts_by_student_and_exam(student_id: int, exam_id: int) -> int:
        """Conteo SARGable y explícitamente parametrizado usando idx_attempt_student_exam_active."""
        stmt = text("""
            SELECT COUNT(id)
            FROM exam_attempts
            WHERE student_id = :student_id
              AND exam_id = :exam_id
              AND is_active = :active_flag
        """).bindparams(
            bindparam("student_id", value=int(student_id), type_=Integer),
            bindparam("exam_id", value=int(exam_id), type_=Integer),
            bindparam("active_flag", value=1, type_=Integer),
        )
        count_val = db.session.execute(stmt).scalar()
        return int(count_val or 0)

    @staticmethod
    def get_attempts_by_student(student_id: int):
        return db.session.query(ExamAttempt).filter_by(
            student_id=student_id, is_active=True
        ).all()

    @staticmethod
    def get_attempts_by_group(group_id: int):
        """Obtiene todos los intentos de un grupo en una sola consulta JOIN SARGable (reemplaza 4 queries secuenciales)."""
        return (
            db.session.query(ExamAttempt)
            .join(Exam, ExamAttempt.exam_id == Exam.id)
            .join(OVA, Exam.ova_id == OVA.id)
            .join(Topic, OVA.topic_id == Topic.id)
            .join(
                Enrollment,
                db.and_(
                    Enrollment.student_id == ExamAttempt.student_id,
                    Enrollment.group_id == Topic.group_id,
                ),
            )
            .filter(
                Topic.group_id == int(group_id),
                Topic.is_active == True,
                OVA.is_active == True,
                Exam.is_active == True,
                Enrollment.is_active == True,
                ExamAttempt.is_active == True,
            )
            .all()
        )

    # ── RESPUESTAS DEL INTENTO ────────────────────────────────────────────────
    @staticmethod
    def create_attempt_answer(answer: AttemptAnswer, commit: bool = True) -> AttemptAnswer:
        return persist_entity(answer, commit=commit)

    @staticmethod
    def get_answers_by_attempt(attempt_id: int):
        return db.session.query(AttemptAnswer).filter_by(
            attempt_id=attempt_id, is_active=True
        ).all()
        
    # ── OBSERVADORES (PRACTICANTES) ───────────────────────────────────────────
    @staticmethod
    def create_observer(observer: GroupObserver, commit: bool = True) -> GroupObserver:
        return persist_entity(observer, commit=commit)

    @staticmethod
    def get_observer_by_id(observer_id: int) -> GroupObserver:
        return db.session.query(GroupObserver).filter_by(
            id=observer_id).first()

    @staticmethod
    def get_observer_by_group_and_user(group_id: int,
                                       observer_id: int) -> GroupObserver:
        return db.session.query(GroupObserver).filter_by(
            group_id=group_id, observer_id=observer_id,
            is_active=True).first()

    @staticmethod
    def get_observer_by_group_and_user_any(group_id: int,
                                           observer_id: int) -> GroupObserver:
        """Busca observador de grupo incluyendo registros inactivos (soft-delete)."""
        return db.session.query(GroupObserver).filter_by(
            group_id=group_id, observer_id=observer_id).first()

    @staticmethod
    def get_observers_by_group(group_id: int):
        return db.session.query(GroupObserver).filter_by(
            group_id=group_id, is_active=True).all()
        
    @staticmethod
    def get_groups_by_user(user_id: int) -> list:
        """Consulta SARGable unificada (UNION indexado) para obtener grupos como docente, estudiante u observador."""
        stmt = text("""
            SELECT g.id AS id
            FROM academic_groups g
            WHERE g.teacher_id = :uid AND g.is_active = :active_flag
            UNION
            SELECT e.group_id AS id
            FROM academic_enrollments e
            INNER JOIN academic_groups g ON g.id = e.group_id
            WHERE e.student_id = :uid AND e.is_active = :active_flag AND g.is_active = :active_flag
            UNION
            SELECT o.group_id AS id
            FROM academic_group_observers o
            INNER JOIN academic_groups g ON g.id = o.group_id
            WHERE o.observer_id = :uid AND o.is_active = :active_flag AND g.is_active = :active_flag
        """).bindparams(
            bindparam("uid", value=int(user_id), type_=Integer),
            bindparam("active_flag", value=1, type_=Integer),
        )
        group_ids = [row[0] for row in db.session.execute(stmt).fetchall()]
        if not group_ids:
            return []
        return (
            db.session.query(Group)
            .filter(Group.id.in_(group_ids), Group.is_active == True)
            .all()
        )

    @staticmethod
    def get_topics_by_group(group_id: int) -> list:
        return Topic.query.filter_by(group_id=group_id, is_active=True).order_by(Topic.order_index).all()

    # ── PROGRESO (TRACKING SILENCIOSO) ────────────────────────────────────
    @staticmethod
    def create_progress(progress, commit: bool = True) -> 'StudentProgress':
        return persist_entity(progress, commit=commit)

    @staticmethod
    def get_group_activity_rows(group_id: int) -> list[dict]:
        """Consulta SARGable y explícitamente parametrizada para el historial de tracking de un grupo."""
        stmt = text("""
            SELECT
                sp.user_id AS user_id,
                sp.ova_id AS ova_id,
                sp.topic_name AS topic_name,
                sp.resource_name AS resource_name,
                sp.action AS action,
                sp.created_at AS created_at,
                o.title AS ova_title,
                p.first_name AS first_name,
                p.last_name AS last_name
            FROM student_progress sp
            INNER JOIN academic_ovas o ON o.id = sp.ova_id
            INNER JOIN academic_topics t ON t.id = o.topic_id
            INNER JOIN academic_enrollments e
                ON e.group_id = t.group_id
               AND e.student_id = sp.user_id
               AND e.is_active = :active_flag
            LEFT JOIN users u ON u.id = sp.user_id
            LEFT JOIN persons p ON p.id = u.person_id
            WHERE t.group_id = :group_id
            ORDER BY sp.created_at DESC
        """).bindparams(
            bindparam("group_id", value=int(group_id), type_=Integer),
            bindparam("active_flag", value=1, type_=Integer),
        )
        rows = db.session.execute(stmt).mappings().all()
        result = []
        for r in rows:
            if r["first_name"] is not None or r["last_name"] is not None:
                student_name = f"{r['first_name'] or ''} {r['last_name'] or ''}"
            else:
                student_name = "Desconocido"

            created_val = r["created_at"]
            ts_iso = (
                created_val.isoformat()
                if hasattr(created_val, "isoformat")
                else str(created_val) if created_val else None
            )
            result.append({
                "user_id": r["user_id"],
                "student_name": student_name,
                "ova_id": r["ova_id"],
                "ova_title": r["ova_title"] if r["ova_title"] else "OVA eliminada",
                "topic_name": r["topic_name"],
                "resource_name": r["resource_name"],
                "action": r["action"],
                "timestamp": ts_iso,
            })
        return result
