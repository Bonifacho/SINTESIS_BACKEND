# app/core_academic/services.py
from datetime import datetime, timezone
from app.extensions import db
from app.utils.database import transactional_session
from app.core_academic.models import (
    Group, Enrollment, Topic,
    OVA, OVAResource, ResourceType,
    Exam, Question, Option, AnswerKey,
    ExamAttempt, AttemptAnswer,
    GroupObserver,
    StudentProgress
)
from app.core_academic.repositories import AcademicRepository


class AcademicService:

    # ── HELPERS DE RESOLUCIÓN JERÁRQUICA Y CONTROL DE ACCESO (SEG-05, SEG-06) ──
    @staticmethod
    def get_group_id_for_topic(topic_id: int) -> int:
        topic = AcademicRepository.get_topic_by_id(topic_id)
        if not topic or not topic.is_active:
            raise ValueError("Tema no encontrado o inactivo")
        return topic.group_id

    @staticmethod
    def get_group_id_for_ova(ova_id: int) -> int:
        ova = AcademicRepository.get_ova_by_id(ova_id)
        if not ova or not ova.is_active:
            raise ValueError("OVA no encontrado o inactivo")
        return AcademicService.get_group_id_for_topic(ova.topic_id)

    @staticmethod
    def get_group_id_for_resource(resource_id: int) -> int:
        resource = AcademicRepository.get_resource_by_id(resource_id)
        if not resource or not resource.is_active:
            raise ValueError("Recurso no encontrado o inactivo")
        return AcademicService.get_group_id_for_ova(resource.ova_id)

    @staticmethod
    def get_group_id_for_exam(exam_id: int) -> int:
        exam = AcademicRepository.get_exam_by_id(exam_id)
        if not exam or not exam.is_active:
            raise ValueError("Examen no encontrado o inactivo")
        return AcademicService.get_group_id_for_ova(exam.ova_id)

    @staticmethod
    def get_group_id_for_question(question_id: int) -> int:
        question = AcademicRepository.get_question_by_id(question_id)
        if not question or not question.is_active:
            raise ValueError("Pregunta no encontrada o inactiva")
        return AcademicService.get_group_id_for_exam(question.exam_id)

    @staticmethod
    def get_group_id_for_option(option_id: int) -> int:
        option = AcademicRepository.get_option_by_id(option_id)
        if not option or not option.is_active:
            raise ValueError("Opción no encontrada o inactiva")
        return AcademicService.get_group_id_for_question(option.question_id)

    @staticmethod
    def get_group_id_for_attempt(attempt_id: int) -> int:
        attempt = AcademicRepository.get_attempt_by_id(attempt_id)
        if not attempt or not attempt.is_active:
            raise ValueError("Intento no encontrado o inactivo")
        return AcademicService.get_group_id_for_exam(attempt.exam_id)

    @staticmethod
    def get_group_id_for_enrollment(enrollment_id: int) -> int:
        enrollment = AcademicRepository.get_enrollment_by_id(enrollment_id)
        if not enrollment or not enrollment.is_active:
            raise ValueError("Matrícula no encontrada o inactiva")
        return enrollment.group_id

    @staticmethod
    def assert_teacher_ownership(group_id: int, user_id: int = None, is_admin: bool = False):
        """Valida que el docente sea el dueño del grupo que intenta modificar (SEG-05).
        Si el usuario es administrador, se permite la operación.
        Si no es dueño ni administrador, lanza PermissionError.
        """
        if is_admin:
            return

        if user_id is None:
            try:
                from flask_jwt_extended import get_jwt_identity, get_jwt
                ident = get_jwt_identity()
                if ident is not None:
                    user_id = int(ident)
                    claims = get_jwt() or {}
                    if 'administrador' in claims.get('roles', []):
                        return
            except Exception:
                return

        if user_id is None:
            return

        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o inactivo")

        if group.teacher_id != user_id:
            raise PermissionError("Acceso denegado: no eres el docente propietario de este grupo")

    @staticmethod
    def can_user_access_group(group_id: int, user_id: int, roles: list = None) -> bool:
        """Verifica si un usuario (docente, practicante, estudiante o admin) tiene acceso a un grupo (SEG-06)."""
        roles = roles or []
        if 'administrador' in roles:
            return True

        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            return False

        if 'docente' in roles and group.teacher_id == user_id:
            return True

        if 'practicante' in roles and AcademicService.check_observer_access(group_id, user_id):
            return True

        if 'estudiante' in roles:
            enrollment = AcademicRepository.get_enrollment_by_student_and_group(user_id, group_id)
            if enrollment and enrollment.is_active:
                return True

        return False

    # ── GRUPOS ────────────────────────────────────────────────────────────────
    @staticmethod
    def create_group(teacher_id: int, name: str) -> dict:
        with transactional_session():
            group = Group(name=name, teacher_id=teacher_id)
            created = AcademicRepository.create_group(group)
        return {
            "id": created.id, "name": created.name,
            "teacher_id": created.teacher_id,
            "created_at": created.created_at.isoformat(),
            "is_active": created.is_active
        }

    @staticmethod
    def get_all_groups() -> list:
        from app.core_security.models import User, Person
        groups = AcademicRepository.get_all_groups()
        # Resolver nombre del docente titular en una sola consulta (vista admin)
        teacher_ids = {g.teacher_id for g in groups if g.teacher_id}
        teacher_names = {}
        if teacher_ids:
            rows = (
                db.session.query(User.id, Person.first_name, Person.last_name)
                .join(Person, User.person_id == Person.id)
                .filter(User.id.in_(teacher_ids))
                .all()
            )
            teacher_names = {r.id: f"{r.first_name} {r.last_name}".strip() for r in rows}
        return [{"id": g.id, "name": g.name, "teacher_id": g.teacher_id,
                 "teacher_name": teacher_names.get(g.teacher_id),
                 "is_active": g.is_active} for g in groups]

    @staticmethod
    def get_group(group_id: int) -> dict:
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o inactivo")
        return {
            "id": group.id,
            "name": group.name,
            "teacher_id": group.teacher_id,
            "is_active": group.is_active
        }

    @staticmethod
    def update_group(group_id: int, new_name: str, user_id: int = None, is_admin: bool = False) -> dict:
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            group = AcademicRepository.get_group_by_id(group_id)
            if not group or not group.is_active:
                raise ValueError("Grupo no encontrado o inactivo")
            group.name = new_name
            db.session.flush()
        return {"id": group.id, "name": group.name, "is_active": group.is_active}

    @staticmethod
    def soft_delete_group(group_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            group = AcademicRepository.get_group_by_id(group_id)
            if not group or not group.is_active:
                raise ValueError("Grupo no encontrado o ya inactivo")
            group.is_active = False
            db.session.flush()
        return {"message": f"Grupo {group_id} desactivado (Soft Delete)"}

    # ── MATRÍCULAS ────────────────────────────────────────────────────────────
    @staticmethod
    def create_enrollment(student_id: int, group_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        from sqlalchemy.exc import IntegrityError
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        try:
            with transactional_session():
                # Bloqueo pesimista sobre el grupo para serializar matrículas concurrentes
                group = AcademicRepository.get_group_by_id_for_update(group_id)
                if not group or not group.is_active:
                    raise ValueError("Grupo no encontrado o inactivo")
                existing = AcademicRepository.get_enrollment_by_student_and_group_any(
                    student_id, group_id)
                if existing:
                    if existing.is_active:
                        raise ValueError("El estudiante ya está matriculado en este grupo")
                    existing.is_active = True
                    existing.enrolled_at = datetime.now(timezone.utc)
                    db.session.flush()
                    created = existing
                else:
                    enrollment = Enrollment(student_id=student_id, group_id=group_id)
                    created = AcademicRepository.create_enrollment(enrollment)
        except IntegrityError:
            raise ValueError("El estudiante ya está matriculado en este grupo")
        return {
            "id": created.id, "student_id": created.student_id,
            "group_id": created.group_id,
            "enrolled_at": created.enrolled_at.isoformat(),
            "is_active": created.is_active
        }

    @staticmethod
    def get_enrollments_by_group(group_id: int) -> list:
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o inactivo")
        return AcademicRepository.get_enrollments_with_students_by_group(group_id)

    @staticmethod
    def get_enrollment_by_id(enrollment_id: int) -> dict:
        e = AcademicRepository.get_enrollment_by_id(enrollment_id)
        if not e or not e.is_active:
            raise ValueError("Matrícula no encontrada o inactiva")
        return {"id": e.id, "student_id": e.student_id,
                "group_id": e.group_id,
                "enrolled_at": e.enrolled_at.isoformat(),
                "is_active": e.is_active}

    @staticmethod
    def update_enrollment(enrollment_id: int, new_group_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        old_group_id = AcademicService.get_group_id_for_enrollment(enrollment_id)
        AcademicService.assert_teacher_ownership(old_group_id, user_id, is_admin)
        AcademicService.assert_teacher_ownership(new_group_id, user_id, is_admin)
        with transactional_session():
            e = AcademicRepository.get_enrollment_by_id(enrollment_id)
            if not e or not e.is_active:
                raise ValueError("Matrícula no encontrada o inactiva")
            new_group = AcademicRepository.get_group_by_id(new_group_id)
            if not new_group or not new_group.is_active:
                raise ValueError("Grupo destino no encontrado o inactivo")
            e.group_id = new_group_id
            db.session.flush()
        return {"id": e.id, "student_id": e.student_id,
                "group_id": e.group_id, "is_active": e.is_active}

    @staticmethod
    def soft_delete_enrollment(enrollment_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_enrollment(enrollment_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            e = AcademicRepository.get_enrollment_by_id(enrollment_id)
            if not e or not e.is_active:
                raise ValueError("Matrícula no encontrada o ya inactiva")
            e.is_active = False
            db.session.flush()
        return {"message": f"Matrícula {enrollment_id} desactivada (Soft Delete)"}

    # ── TEMAS ─────────────────────────────────────────────────────────────────
    @staticmethod
    def create_topic(group_id: int, title: str, order_index: int = 0, user_id: int = None, is_admin: bool = False) -> dict:
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o inactivo")
        with transactional_session():
            topic = Topic(title=title, group_id=group_id, order_index=order_index)
            created = AcademicRepository.create_topic(topic)
        return {"id": created.id, "title": created.title,
                "group_id": created.group_id,
                "order_index": created.order_index,
                "is_active": created.is_active}

    @staticmethod
    def update_topic(topic_id: int, new_title: str, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_topic(topic_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            topic = AcademicRepository.get_topic_by_id(topic_id)
            if not topic or not topic.is_active:
                raise ValueError("Tema no encontrado o inactivo")
            topic.title = new_title
            db.session.flush()
        return {"id": topic.id, "title": topic.title,
                "is_active": topic.is_active}

    @staticmethod
    def soft_delete_topic(topic_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_topic(topic_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            topic = AcademicRepository.get_topic_by_id(topic_id)
            if not topic or not topic.is_active:
                raise ValueError("Tema no encontrado o ya inactivo")
            topic.is_active = False
            db.session.flush()
        return {"message": f"Tema {topic_id} desactivado (Soft Delete)"}

    # ── OVAs ──────────────────────────────────────────────────────────────────
    @staticmethod
    def create_ova(topic_id: int, title: str, description: str = None,
                   order_index: int = 0, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_topic(topic_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        topic = AcademicRepository.get_topic_by_id(topic_id)
        if not topic or not topic.is_active:
            raise ValueError("Tema no encontrado o inactivo")
        with transactional_session():
            ova = OVA(title=title, description=description,
                      topic_id=topic_id, order_index=order_index)
            created = AcademicRepository.create_ova(ova)
        return {"id": created.id, "title": created.title,
                "description": created.description,
                "topic_id": created.topic_id,
                "order_index": created.order_index,
                "is_active": created.is_active}

    @staticmethod
    def get_ova_by_id(ova_id: int) -> dict:
        ova = AcademicRepository.get_ova_by_id(ova_id)
        if not ova or not ova.is_active:
            raise ValueError("OVA no encontrado o inactivo")
        resources = AcademicRepository.get_resources_by_ova(ova_id)
        return {
            "id": ova.id, "title": ova.title,
            "description": ova.description,
            "topic_id": ova.topic_id,
            "order_index": ova.order_index,
            "is_active": ova.is_active,
            "resources": [
                {"id": r.id, "resource_type": r.resource_type.value,
                 "display_title": r.display_title, "url": r.url,
                 "content": r.content, "order_index": r.order_index}
                for r in resources
            ]
        }

    @staticmethod
    def update_ova(ova_id: int, data: dict, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_ova(ova_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            ova = AcademicRepository.get_ova_by_id(ova_id)
            if not ova or not ova.is_active:
                raise ValueError("OVA no encontrado o inactivo")
            if 'title' in data:
                ova.title = data['title']
            if 'description' in data:
                ova.description = data['description']
            if 'order_index' in data:
                ova.order_index = data['order_index']
            db.session.flush()
        return {"id": ova.id, "title": ova.title,
                "description": ova.description, "is_active": ova.is_active}

    @staticmethod
    def soft_delete_ova(ova_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_ova(ova_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            ova = AcademicRepository.get_ova_by_id(ova_id)
            if not ova or not ova.is_active:
                raise ValueError("OVA no encontrado o ya inactivo")
            ova.is_active = False
            db.session.flush()
        return {"message": f"OVA {ova_id} desactivado (Soft Delete)"}

    # ── RECURSOS ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_resource(ova_id: int, resource_type: str, display_title: str,
                        url: str = None, content: str = None,
                        order_index: int = 0, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_ova(ova_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        ova = AcademicRepository.get_ova_by_id(ova_id)
        if not ova or not ova.is_active:
            raise ValueError("OVA no encontrado o inactivo")
        try:
            rtype = ResourceType[resource_type]
        except KeyError:
            raise ValueError(
                f"Tipo inválido. Use: {[e.value for e in ResourceType]}")
        with transactional_session():
            resource = OVAResource(
                ova_id=ova_id, resource_type=rtype,
                display_title=display_title, url=url,
                content=content, order_index=order_index
            )
            created = AcademicRepository.create_resource(resource)
        return {"id": created.id, "ova_id": created.ova_id,
                "resource_type": created.resource_type.value,
                "display_title": created.display_title,
                "url": created.url, "content": created.content,
                "order_index": created.order_index,
                "is_active": created.is_active}

    @staticmethod
    def update_resource(resource_id: int, data: dict, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_resource(resource_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            r = AcademicRepository.get_resource_by_id(resource_id)
            if not r or not r.is_active:
                raise ValueError("Recurso no encontrado o inactivo")
            if 'display_title' in data:
                r.display_title = data['display_title']
            if 'url' in data:
                r.url = data['url']
            if 'content' in data:
                r.content = data['content']
            if 'order_index' in data:
                r.order_index = data['order_index']
            db.session.flush()
        return {"id": r.id, "display_title": r.display_title,
                "resource_type": r.resource_type.value,
                "is_active": r.is_active}

    @staticmethod
    def soft_delete_resource(resource_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_resource(resource_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            r = AcademicRepository.get_resource_by_id(resource_id)
            if not r or not r.is_active:
                raise ValueError("Recurso no encontrado o ya inactivo")
            r.is_active = False
            db.session.flush()
        return {"message": f"Recurso {resource_id} desactivado (Soft Delete)"}

    # ── EXÁMENES ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_exam(ova_id: int, title: str, passing_score: int = 60,
                    max_attempts: int = 3, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_ova(ova_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        ova = AcademicRepository.get_ova_by_id(ova_id)
        if not ova or not ova.is_active:
            raise ValueError("OVA no encontrado o inactivo")
        with transactional_session():
            existing = AcademicRepository.get_exam_by_ova_any(ova_id)
            if existing:
                if existing.is_active:
                    raise ValueError("Este OVA ya tiene un examen asignado")
                existing.is_active = True
                existing.title = title
                existing.passing_score = passing_score
                existing.max_attempts = max_attempts
                db.session.flush()
                created = existing
            else:
                exam = Exam(ova_id=ova_id, title=title,
                            passing_score=passing_score, max_attempts=max_attempts)
                created = AcademicRepository.create_exam(exam)
        return {"id": created.id, "ova_id": created.ova_id,
                "title": created.title,
                "passing_score": created.passing_score,
                "max_attempts": created.max_attempts,
                "is_active": created.is_active}

    @staticmethod
    def update_exam(exam_id: int, data: dict, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_exam(exam_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            exam = AcademicRepository.get_exam_by_id(exam_id)
            if not exam or not exam.is_active:
                raise ValueError("Examen no encontrado o inactivo")
            if 'title' in data:
                exam.title = data['title']
            if 'passing_score' in data:
                exam.passing_score = data['passing_score']
            if 'max_attempts' in data:
                exam.max_attempts = data['max_attempts']
            db.session.flush()
        return {"id": exam.id, "title": exam.title,
                "passing_score": exam.passing_score,
                "max_attempts": exam.max_attempts,
                "is_active": exam.is_active}

    @staticmethod
    def soft_delete_exam(exam_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_exam(exam_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            exam = AcademicRepository.get_exam_by_id(exam_id)
            if not exam or not exam.is_active:
                raise ValueError("Examen no encontrado o ya inactivo")
            exam.is_active = False
            db.session.flush()
        return {"message": f"Examen {exam_id} desactivado (Soft Delete)"}

    # ── PREGUNTAS ─────────────────────────────────────────────────────────────
    @staticmethod
    def create_question(exam_id: int, statement: str, points: int = 1,
                        order_index: int = 0, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_exam(exam_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        exam = AcademicRepository.get_exam_by_id(exam_id)
        if not exam or not exam.is_active:
            raise ValueError("Examen no encontrado o inactivo")
        with transactional_session():
            question = Question(exam_id=exam_id, statement=statement,
                                points=points, order_index=order_index)
            created = AcademicRepository.create_question(question)
        return {"id": created.id, "exam_id": created.exam_id,
                "statement": created.statement,
                "points": created.points,
                "order_index": created.order_index,
                "is_active": created.is_active}

    @staticmethod
    def update_question(question_id: int, data: dict, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_question(question_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            q = AcademicRepository.get_question_by_id(question_id)
            if not q or not q.is_active:
                raise ValueError("Pregunta no encontrada o inactiva")
            if 'statement' in data:
                q.statement = data['statement']
            if 'points' in data:
                q.points = data['points']
            if 'order_index' in data:
                q.order_index = data['order_index']
            db.session.flush()
        return {"id": q.id, "statement": q.statement,
                "points": q.points, "is_active": q.is_active}

    @staticmethod
    def soft_delete_question(question_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_question(question_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            q = AcademicRepository.get_question_by_id(question_id)
            if not q or not q.is_active:
                raise ValueError("Pregunta no encontrada o ya inactiva")
            q.is_active = False
            db.session.flush()
        return {"message": f"Pregunta {question_id} desactivada (Soft Delete)"}

    # ── OPCIONES ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_option(question_id: int, text: str,
                      order_index: int = 0, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_question(question_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        q = AcademicRepository.get_question_by_id(question_id)
        if not q or not q.is_active:
            raise ValueError("Pregunta no encontrada o inactiva")
        with transactional_session():
            option = Option(question_id=question_id, text=text,
                            order_index=order_index)
            created = AcademicRepository.create_option(option)
        return {"id": created.id, "question_id": created.question_id,
                "text": created.text, "order_index": created.order_index,
                "is_active": created.is_active}

    @staticmethod
    def update_option(option_id: int, data: dict, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_option(option_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            o = AcademicRepository.get_option_by_id(option_id)
            if not o or not o.is_active:
                raise ValueError("Opción no encontrada o inactiva")
            if 'text' in data:
                o.text = data['text']
            if 'order_index' in data:
                o.order_index = data['order_index']
            db.session.flush()
        return {"id": o.id, "text": o.text, "is_active": o.is_active}

    @staticmethod
    def soft_delete_option(option_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_option(option_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            o = AcademicRepository.get_option_by_id(option_id)
            if not o or not o.is_active:
                raise ValueError("Opción no encontrada o ya inactiva")
            o.is_active = False
            db.session.flush()
        return {"message": f"Opción {option_id} desactivada (Soft Delete)"}

    # ── CLAVE DE RESPUESTAS ───────────────────────────────────────────────────
    @staticmethod
    def set_answer_key(question_id: int, correct_option_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        group_id = AcademicService.get_group_id_for_question(question_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        q = AcademicRepository.get_question_by_id(question_id)
        if not q or not q.is_active:
            raise ValueError("Pregunta no encontrada o inactiva")
        option = AcademicRepository.get_option_by_id(correct_option_id)
        if not option or option.question_id != question_id:
            raise ValueError("La opción no pertenece a esta pregunta")
        with transactional_session():
            existing = AcademicRepository.get_answer_key_by_question_any(question_id)
            if existing:
                was_active = existing.is_active
                existing.correct_option_id = correct_option_id
                existing.is_active = True
                db.session.flush()
                return {"message": "Clave actualizada" if was_active else "Clave registrada",
                        "question_id": question_id,
                        "correct_option_id": correct_option_id}
            key = AnswerKey(question_id=question_id,
                            correct_option_id=correct_option_id)
            AcademicRepository.create_answer_key(key)
        return {"message": "Clave registrada",
                "question_id": question_id,
                "correct_option_id": correct_option_id}

    # ── INTENTOS Y CALIFICACIÓN INMUTABLE ─────────────────────────────────────
    @staticmethod
    def start_attempt(student_id: int, exam_id: int) -> dict:
        with transactional_session():
            # Bloqueo pesimista SELECT ... FOR UPDATE sobre el examen para serializar cupos concurrentes
            exam = AcademicRepository.get_exam_by_id_for_update(exam_id)
            if not exam or not exam.is_active:
                raise ValueError("Examen no encontrado o inactivo")
            # Validar que el estudiante esté matriculado en el grupo correspondiente al examen
            group_id = AcademicService.get_group_id_for_exam(exam_id)
            enrollment = AcademicRepository.get_enrollment_by_student_and_group(student_id, group_id)
            if not enrollment or not enrollment.is_active:
                raise PermissionError("El estudiante no está matriculado en el grupo de este examen")
            
            # Validar completitud del examen antes de permitir iniciar el intento (BE-02)
            questions = AcademicRepository.get_questions_by_exam(exam_id)
            if not questions:
                raise ValueError("El examen no tiene preguntas configuradas.")
            
            answer_keys = AcademicRepository.get_answer_keys_by_exam(exam_id)
            key_map = {k.question_id: k.correct_option_id for k in answer_keys if k.is_active}
            missing_keys = [q.id for q in questions if q.id not in key_map or key_map[q.id] is None]
            if missing_keys:
                raise ValueError(f"El examen tiene {len(missing_keys)} pregunta(s) sin clave de respuesta configurada.")

            # Conteo SARGable y explícitamente parametrizado (covering index idx_attempt_student_exam_active)
            previous_count = AcademicRepository.count_attempts_by_student_and_exam(
                student_id, exam_id)
            if previous_count >= exam.max_attempts:
                raise ValueError(
                    f"Se alcanzó el límite de {exam.max_attempts} intento(s)")
            attempt = ExamAttempt(exam_id=exam_id, student_id=student_id)
            created = AcademicRepository.create_attempt(attempt)
        return {"id": created.id, "exam_id": created.exam_id,
                "student_id": created.student_id,
                "started_at": created.started_at.isoformat(),
                "submitted_at": None}

    @staticmethod
    def submit_attempt(attempt_id: int, answers: list, student_id: int = None) -> dict:
        with transactional_session():
            # Bloqueo pesimista SELECT ... FOR UPDATE sobre el intento para evitar doble envío concurrente
            attempt = AcademicRepository.get_attempt_by_id_for_update(attempt_id)
            if not attempt or not attempt.is_active:
                raise ValueError("Intento no encontrado o inactivo")
            if student_id is not None and attempt.student_id != student_id:
                raise PermissionError("Acceso denegado: este intento pertenece a otro estudiante")
            if attempt.submitted_at:
                raise ValueError("Este intento ya fue enviado")
            for ans in answers:
                attempt_answer = AttemptAnswer(
                    attempt_id=attempt_id,
                    question_id=ans['question_id'],
                    selected_option_id=ans['selected_option_id']
                )
                db.session.add(attempt_answer)
            attempt.submitted_at = datetime.now(timezone.utc)

            # Calcular y congelar el snapshot inmutable de calificación (BE-01, BE-03)
            questions = AcademicRepository.get_questions_by_exam(attempt.exam_id)
            answer_keys = AcademicRepository.get_answer_keys_by_exam(attempt.exam_id)
            key_map = {k.question_id: k.correct_option_id for k in answer_keys if k.is_active}
            student_map = {ans['question_id']: ans['selected_option_id'] for ans in answers}

            total_possible = sum(q.points for q in questions) if questions else 0
            earned = 0
            for q in questions:
                correct_opt = key_map.get(q.id)
                selected_opt = student_map.get(q.id)
                if correct_opt is not None and selected_opt == correct_opt:
                    earned += q.points

            score = round((earned / total_possible) * 100) if total_possible > 0 else 0
            exam = AcademicRepository.get_exam_by_id(attempt.exam_id)
            passed = score >= (exam.passing_score if exam else 60)

            # Persistir snapshot inmutable
            attempt.score = score
            attempt.passed = passed
            attempt.total_questions = len(questions)
            attempt.total_points = total_possible
            attempt.earned_points = earned
            db.session.flush()

        return AcademicService._calculate_result(attempt_id)

    @staticmethod
    def get_attempt_result(attempt_id: int, user_id: int = None, roles: list = None) -> dict:
        attempt = AcademicRepository.get_attempt_by_id(attempt_id)
        if not attempt or not attempt.submitted_at or not attempt.is_active:
            raise ValueError("Intento no encontrado o aún no enviado")
        if user_id is not None and roles:
            if 'estudiante' in roles and not any(r in roles for r in ['administrador', 'docente', 'practicante']):
                if attempt.student_id != user_id:
                    raise PermissionError("Acceso denegado: este resultado no te pertenece")
            elif any(r in roles for r in ['docente', 'practicante']) and 'administrador' not in roles:
                group_id = AcademicService.get_group_id_for_attempt(attempt_id)
                if not AcademicService.can_user_access_group(group_id, user_id, roles):
                    raise PermissionError("Acceso denegado al grupo de este intento")
        return AcademicService._calculate_result(attempt_id)

    @staticmethod
    def soft_delete_attempt(attempt_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        """Permite a un docente resetear (invalidar) un intento para liberar cupo al estudiante."""
        group_id = AcademicService.get_group_id_for_attempt(attempt_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        with transactional_session():
            attempt = AcademicRepository.get_attempt_by_id(attempt_id)
            if not attempt or not attempt.is_active:
                raise ValueError("Intento no encontrado o ya reseteado")
            attempt.is_active = False
            db.session.flush()
        return {"message": f"Intento {attempt_id} reseteado exitosamente"}

    @staticmethod
    def _calculate_result(attempt_id: int) -> dict:
        attempt = AcademicRepository.get_attempt_by_id(attempt_id)
        exam = AcademicRepository.get_exam_by_id(attempt.exam_id)
        if not attempt.submitted_at:
            return {
                "attempt_id": attempt_id,
                "exam_id": attempt.exam_id,
                "ova_id": exam.ova_id if exam else None,
                "student_id": attempt.student_id,
                "score": 0,
                "passed": False,
                "correct_answers": 0,
                "total_questions": 0,
                "total_points": 0,
                "earned_points": 0,
                "passing_score": exam.passing_score if exam else 0,
                "submitted_at": None,
                "status": "in_progress",
                "question_results": []
            }
        student_answers = AcademicRepository.get_answers_by_attempt(attempt_id)
        student_map = {a.question_id: a.selected_option_id
                       for a in student_answers}
        answer_keys = AcademicRepository.get_answer_keys_by_exam(attempt.exam_id)
        key_map = {k.question_id: k.correct_option_id for k in answer_keys if k.is_active}
        
        questions = AcademicRepository.get_questions_by_exam(attempt.exam_id)
        # Carga en lote (batch loading) de todas las opciones del examen en 1 sola consulta SARGable
        options_by_q = AcademicRepository.get_options_by_questions([q.id for q in questions])
        correct_count = 0
        earned_calculated = 0
        total_possible = sum(q.points for q in questions) if questions else 0
        question_results = []
        
        for q in questions:
            qid = q.id
            correct_opt = key_map.get(qid)
            selected_opt = student_map.get(qid)
            is_correct = (selected_opt == correct_opt) if correct_opt is not None else False
            
            if is_correct:
                correct_count += 1
                earned_calculated += q.points
                
            options = options_by_q.get(qid, [])
            opt_map = {o.id: o.text for o in options}
            
            question_results.append({
                "question_id": qid,
                "statement": q.statement,
                "points": q.points,
                "selected_option_id": selected_opt,
                "selected_option_text": opt_map.get(selected_opt) if selected_opt else None,
                "correct_option_id": correct_opt,
                "correct_option_text": opt_map.get(correct_opt) if correct_opt else None,
                "is_correct": is_correct
            })
            
        # Snapshot inmutable (BE-03): si ya está persistido, usamos el snapshot
        if attempt.score is not None:
            score = attempt.score
            passed = attempt.passed if attempt.passed is not None else (score >= exam.passing_score if exam else False)
            total_questions = attempt.total_questions or len(questions)
            total_points = attempt.total_points if attempt.total_points is not None else total_possible
            earned_points = attempt.earned_points if attempt.earned_points is not None else earned_calculated
        else:
            # Backfill para intentos históricos
            score = round((earned_calculated / total_possible) * 100) if total_possible > 0 else 0
            passed = score >= exam.passing_score if exam else False
            total_questions = len(questions)
            total_points = total_possible
            earned_points = earned_calculated
            with transactional_session():
                attempt.score = score
                attempt.passed = passed
                attempt.total_questions = total_questions
                attempt.total_points = total_points
                attempt.earned_points = earned_points
                db.session.flush()

        # Obtener título del OVA para filtrado en historial
        ova_title = None
        if exam and exam.ova_id:
            ova = AcademicRepository.get_ova_by_id(exam.ova_id)
            ova_title = ova.title if ova else None
        return {
            "attempt_id": attempt_id,
            "exam_id": attempt.exam_id,
            "ova_id": exam.ova_id if exam else None,
            "ova_title": ova_title,
            "student_id": attempt.student_id,
            "score": score,
            "passed": passed,
            "correct_answers": correct_count,
            "total_questions": total_questions,
            "total_points": total_points,
            "earned_points": earned_points,
            "passing_score": exam.passing_score if exam else 0,
            "submitted_at": attempt.submitted_at.isoformat(),
            "status": "completed",
            "question_results": question_results
        }
        
# ── OBSERVADORES (PRACTICANTES) ───────────────────────────────────────────
    @staticmethod
    def assign_observer(group_id: int, observer_id: int,
                        assigned_by: int, is_admin: bool = False) -> dict:
        """Docente asigna un practicante a un grupo."""
        AcademicService.assert_teacher_ownership(group_id, user_id=assigned_by, is_admin=is_admin)
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o inactivo")

        with transactional_session():
            existing = AcademicRepository.get_observer_by_group_and_user_any(
                group_id, observer_id)
            if existing:
                if existing.is_active:
                    raise ValueError("Este practicante ya tiene acceso a ese grupo")
                existing.is_active = True
                existing.assigned_by = assigned_by
                db.session.flush()
                created = existing
            else:
                observer = GroupObserver(
                    group_id=group_id,
                    observer_id=observer_id,
                    assigned_by=assigned_by
                )
                created = AcademicRepository.create_observer(observer)
        return {
            "id": created.id,
            "group_id": created.group_id,
            "observer_id": created.observer_id,
            "assigned_by": created.assigned_by,
            "created_at": created.created_at.isoformat(),
            "is_active": created.is_active
        }

    @staticmethod
    def revoke_observer(observer_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        """Docente revoca el acceso de un practicante."""
        observer = AcademicRepository.get_observer_by_id(observer_id)
        if not observer or not observer.is_active:
            raise ValueError("Acceso no encontrado o ya revocado")
        AcademicService.assert_teacher_ownership(observer.group_id, user_id=user_id, is_admin=is_admin)
        with transactional_session():
            observer.is_active = False
            db.session.flush()
        return {"message": f"Acceso del practicante {observer_id} revocado"}

    @staticmethod
    def get_observers_by_group(group_id: int) -> list:
        """Lista todos los practicantes asignados a un grupo."""
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o inactivo")
        observers = AcademicRepository.get_observers_by_group(group_id)
        return [{
            "id": o.id,
            "observer_id": o.observer_id,
            "assigned_by": o.assigned_by,
            "created_at": o.created_at.isoformat(),
            "is_active": o.is_active
        } for o in observers]

    @staticmethod
    def check_observer_access(group_id: int, user_id: int) -> bool:
        """Verifica si un practicante tiene acceso a un grupo específico."""
        result = AcademicRepository.get_observer_by_group_and_user(
            group_id, user_id)
        return result is not None
    
    @staticmethod
    def get_user_groups(user_id: int) -> list:
        groups = AcademicRepository.get_groups_by_user(user_id)
        return [{"id": g.id, "name": g.name, "teacher_id": g.teacher_id} for g in groups]

    @staticmethod
    def get_group_topics(group_id: int) -> list:
        topics = AcademicRepository.get_topics_by_group(group_id)
        return [{"id": t.id, "title": t.title, "order_index": t.order_index} for t in topics]

    @staticmethod
    def get_ovas_by_topic(topic_id: int) -> list:
        ovas = AcademicRepository.get_ovas_by_topic(topic_id)
        if not ovas:
            return []
        ova_ids = [o.id for o in ovas]
        resources_by_ova = AcademicRepository.get_resources_by_ovas(ova_ids)
        exams_by_ova = AcademicRepository.get_exams_by_ovas(ova_ids)

        result = []
        for o in ovas:
            res_list = [
                {
                    "id": r.id,
                    "resource_type": r.resource_type.value,
                    "url": r.url,
                    "content": r.content,
                    "display_title": r.display_title,
                    "order_index": r.order_index,
                }
                for r in resources_by_ova.get(o.id, [])
            ]
            exam = exams_by_ova.get(o.id)
            has_exam = exam is not None and exam.is_active

            result.append({
                "id": o.id,
                "title": o.title,
                "description": o.description,
                "order_index": o.order_index,
                "resources": res_list,
                "has_exam": has_exam,
                "exam_id": exam.id if has_exam else None,
                "exam_title": exam.title if has_exam else None
            })
        return result

    @staticmethod
    def get_exam_by_ova_full(ova_id: int) -> dict:
        exam = AcademicRepository.get_exam_by_ova(ova_id)
        if not exam or not exam.is_active:
            raise ValueError("Examen no encontrado o inactivo")
        questions = AcademicRepository.get_questions_by_exam(exam.id)
        options_by_q = AcademicRepository.get_options_by_questions([q.id for q in questions])
        qs_data = []
        for q in questions:
            options = options_by_q.get(q.id, [])
            qs_data.append({
                "id": q.id,
                "statement": q.statement,
                "points": q.points,
                "order_index": q.order_index,
                "options": [{"id": o.id, "text": o.text, "order_index": o.order_index} for o in options]
            })
        return {
            "id": exam.id,
            "title": exam.title,
            "passing_score": exam.passing_score,
            "max_attempts": exam.max_attempts,
            "questions": qs_data
        }

    @staticmethod
    def get_exam_by_ova_teacher(ova_id: int, user_id: int = None, is_admin: bool = False) -> dict:
        """Versión exclusiva para docentes que incluye correct_option_id."""
        group_id = AcademicService.get_group_id_for_ova(ova_id)
        AcademicService.assert_teacher_ownership(group_id, user_id, is_admin)
        exam = AcademicRepository.get_exam_by_ova(ova_id)
        if not exam or not exam.is_active:
            raise ValueError("Examen no encontrado o inactivo")
        questions = AcademicRepository.get_questions_by_exam(exam.id)
        options_by_q = AcademicRepository.get_options_by_questions([q.id for q in questions])
        answer_keys = AcademicRepository.get_answer_keys_by_exam(exam.id)
        key_map = {k.question_id: k.correct_option_id for k in answer_keys if k.is_active}
        qs_data = []
        for q in questions:
            options = options_by_q.get(q.id, [])
            correct_option_id = key_map.get(q.id)
            qs_data.append({
                "id": q.id,
                "statement": q.statement,
                "points": q.points,
                "order_index": q.order_index,
                "correct_option_id": correct_option_id,
                "options": [{"id": o.id, "text": o.text, "order_index": o.order_index} for o in options]
            })
        return {
            "id": exam.id,
            "title": exam.title,
            "passing_score": exam.passing_score,
            "max_attempts": exam.max_attempts,
            "questions": qs_data
        }

    @staticmethod
    def get_attempts_by_student(student_id: int) -> list:
        attempts = AcademicRepository.get_attempts_by_student(student_id)
        return [AcademicService._calculate_result(a.id) for a in attempts]

    @staticmethod
    def get_group_activity(group_id: int) -> list:
        """Retorna el historial de tracking silencioso de un grupo mediante una sola consulta SARGable."""
        return AcademicRepository.get_group_activity_rows(group_id)

    @staticmethod
    def get_attempts_by_group(group_id: int) -> list:
        attempts = AcademicRepository.get_attempts_by_group(group_id)
        return [AcademicService._calculate_result(a.id) for a in attempts]

    # ── PROGRESO (TRACKING SILENCIOSO) ────────────────────────────────────
    VALID_ACTIONS = {"exam_started", "exam_opened", "resource_opened"}

    @staticmethod
    def register_progress(user_id: int, ova_id: int, action: str, topic_name: str = None, resource_name: str = None) -> dict:
        """Registra un evento de acceso silencioso del estudiante."""
        if action not in AcademicService.VALID_ACTIONS:
            raise ValueError(
                f"Acción inválida '{action}'. "
                f"Valores permitidos: {AcademicService.VALID_ACTIONS}")
        ova = AcademicRepository.get_ova_by_id(ova_id)
        if not ova or not ova.is_active:
            raise ValueError("OVA no encontrado o inactivo")
        with transactional_session():
            progress = StudentProgress(
                user_id=user_id, ova_id=ova_id, action=action,
                topic_name=topic_name, resource_name=resource_name)
            created = AcademicRepository.create_progress(progress)
        return {
            "id": created.id,
            "user_id": created.user_id,
            "ova_id": created.ova_id,
            "action": created.action,
            "topic_name": created.topic_name,
            "resource_name": created.resource_name,
            "created_at": created.created_at.isoformat() if created.created_at else None
        }