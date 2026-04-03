# app/core_academic/services.py
from datetime import datetime, timezone
from app.extensions import db
from app.core_academic.models import (
    Group, Enrollment, Topic,
    OVA, OVAResource, ResourceType,
    Exam, Question, Option, AnswerKey,
    ExamAttempt, AttemptAnswer
)
from app.core_academic.repositories import AcademicRepository


class AcademicService:

    # ── GRUPOS ────────────────────────────────────────────────────────────────
    @staticmethod
    def create_group(teacher_id: int, name: str) -> dict:
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
        groups = AcademicRepository.get_all_groups()
        return [{"id": g.id, "name": g.name, "teacher_id": g.teacher_id,
                 "is_active": g.is_active} for g in groups]

    @staticmethod
    def update_group(group_id: int, new_name: str) -> dict:
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o inactivo")
        group.name = new_name
        db.session.commit()
        return {"id": group.id, "name": group.name, "is_active": group.is_active}

    @staticmethod
    def soft_delete_group(group_id: int) -> dict:
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o ya inactivo")
        group.is_active = False
        db.session.commit()
        return {"message": f"Grupo {group_id} desactivado (Soft Delete)"}

    # ── MATRÍCULAS ────────────────────────────────────────────────────────────
    @staticmethod
    def create_enrollment(student_id: int, group_id: int) -> dict:
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o inactivo")
        existing = AcademicRepository.get_enrollment_by_student_and_group(
            student_id, group_id)
        if existing:
            raise ValueError("El estudiante ya está matriculado en este grupo")
        enrollment = Enrollment(student_id=student_id, group_id=group_id)
        created = AcademicRepository.create_enrollment(enrollment)
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
        enrollments = AcademicRepository.get_enrollments_by_group(group_id)
        return [{"id": e.id, "student_id": e.student_id,
                 "group_id": e.group_id,
                 "enrolled_at": e.enrolled_at.isoformat(),
                 "is_active": e.is_active} for e in enrollments]

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
    def update_enrollment(enrollment_id: int, new_group_id: int) -> dict:
        e = AcademicRepository.get_enrollment_by_id(enrollment_id)
        if not e or not e.is_active:
            raise ValueError("Matrícula no encontrada o inactiva")
        new_group = AcademicRepository.get_group_by_id(new_group_id)
        if not new_group or not new_group.is_active:
            raise ValueError("Grupo destino no encontrado o inactivo")
        e.group_id = new_group_id
        db.session.commit()
        return {"id": e.id, "student_id": e.student_id,
                "group_id": e.group_id, "is_active": e.is_active}

    @staticmethod
    def soft_delete_enrollment(enrollment_id: int) -> dict:
        e = AcademicRepository.get_enrollment_by_id(enrollment_id)
        if not e or not e.is_active:
            raise ValueError("Matrícula no encontrada o ya inactiva")
        e.is_active = False
        db.session.commit()
        return {"message": f"Matrícula {enrollment_id} desactivada (Soft Delete)"}

    # ── TEMAS ─────────────────────────────────────────────────────────────────
    @staticmethod
    def create_topic(group_id: int, title: str, order_index: int = 0) -> dict:
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o inactivo")
        topic = Topic(title=title, group_id=group_id, order_index=order_index)
        created = AcademicRepository.create_topic(topic)
        return {"id": created.id, "title": created.title,
                "group_id": created.group_id,
                "order_index": created.order_index,
                "is_active": created.is_active}

    @staticmethod
    def update_topic(topic_id: int, new_title: str) -> dict:
        topic = AcademicRepository.get_topic_by_id(topic_id)
        if not topic or not topic.is_active:
            raise ValueError("Tema no encontrado o inactivo")
        topic.title = new_title
        db.session.commit()
        return {"id": topic.id, "title": topic.title,
                "is_active": topic.is_active}

    @staticmethod
    def soft_delete_topic(topic_id: int) -> dict:
        topic = AcademicRepository.get_topic_by_id(topic_id)
        if not topic or not topic.is_active:
            raise ValueError("Tema no encontrado o ya inactivo")
        topic.is_active = False
        db.session.commit()
        return {"message": f"Tema {topic_id} desactivado (Soft Delete)"}

    # ── OVAs ──────────────────────────────────────────────────────────────────
    @staticmethod
    def create_ova(topic_id: int, title: str, description: str = None,
                   order_index: int = 0) -> dict:
        topic = AcademicRepository.get_topic_by_id(topic_id)
        if not topic or not topic.is_active:
            raise ValueError("Tema no encontrado o inactivo")
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
    def update_ova(ova_id: int, data: dict) -> dict:
        ova = AcademicRepository.get_ova_by_id(ova_id)
        if not ova or not ova.is_active:
            raise ValueError("OVA no encontrado o inactivo")
        if 'title' in data:
            ova.title = data['title']
        if 'description' in data:
            ova.description = data['description']
        if 'order_index' in data:
            ova.order_index = data['order_index']
        db.session.commit()
        return {"id": ova.id, "title": ova.title,
                "description": ova.description, "is_active": ova.is_active}

    @staticmethod
    def soft_delete_ova(ova_id: int) -> dict:
        ova = AcademicRepository.get_ova_by_id(ova_id)
        if not ova or not ova.is_active:
            raise ValueError("OVA no encontrado o ya inactivo")
        ova.is_active = False
        db.session.commit()
        return {"message": f"OVA {ova_id} desactivado (Soft Delete)"}

    # ── RECURSOS ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_resource(ova_id: int, resource_type: str, display_title: str,
                        url: str = None, content: str = None,
                        order_index: int = 0) -> dict:
        ova = AcademicRepository.get_ova_by_id(ova_id)
        if not ova or not ova.is_active:
            raise ValueError("OVA no encontrado o inactivo")
        try:
            rtype = ResourceType[resource_type]
        except KeyError:
            raise ValueError(
                f"Tipo inválido. Use: {[e.value for e in ResourceType]}")
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
    def update_resource(resource_id: int, data: dict) -> dict:
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
        db.session.commit()
        return {"id": r.id, "display_title": r.display_title,
                "resource_type": r.resource_type.value,
                "is_active": r.is_active}

    @staticmethod
    def soft_delete_resource(resource_id: int) -> dict:
        r = AcademicRepository.get_resource_by_id(resource_id)
        if not r or not r.is_active:
            raise ValueError("Recurso no encontrado o ya inactivo")
        r.is_active = False
        db.session.commit()
        return {"message": f"Recurso {resource_id} desactivado (Soft Delete)"}

    # ── EXÁMENES ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_exam(ova_id: int, title: str, passing_score: int = 60,
                    max_attempts: int = 3) -> dict:
        ova = AcademicRepository.get_ova_by_id(ova_id)
        if not ova or not ova.is_active:
            raise ValueError("OVA no encontrado o inactivo")
        if AcademicRepository.get_exam_by_ova(ova_id):
            raise ValueError("Este OVA ya tiene un examen asignado")
        exam = Exam(ova_id=ova_id, title=title,
                    passing_score=passing_score, max_attempts=max_attempts)
        created = AcademicRepository.create_exam(exam)
        return {"id": created.id, "ova_id": created.ova_id,
                "title": created.title,
                "passing_score": created.passing_score,
                "max_attempts": created.max_attempts,
                "is_active": created.is_active}

    @staticmethod
    def update_exam(exam_id: int, data: dict) -> dict:
        exam = AcademicRepository.get_exam_by_id(exam_id)
        if not exam or not exam.is_active:
            raise ValueError("Examen no encontrado o inactivo")
        if 'title' in data:
            exam.title = data['title']
        if 'passing_score' in data:
            exam.passing_score = data['passing_score']
        if 'max_attempts' in data:
            exam.max_attempts = data['max_attempts']
        db.session.commit()
        return {"id": exam.id, "title": exam.title,
                "passing_score": exam.passing_score,
                "max_attempts": exam.max_attempts,
                "is_active": exam.is_active}

    @staticmethod
    def soft_delete_exam(exam_id: int) -> dict:
        exam = AcademicRepository.get_exam_by_id(exam_id)
        if not exam or not exam.is_active:
            raise ValueError("Examen no encontrado o ya inactivo")
        exam.is_active = False
        db.session.commit()
        return {"message": f"Examen {exam_id} desactivado (Soft Delete)"}

    # ── PREGUNTAS ─────────────────────────────────────────────────────────────
    @staticmethod
    def create_question(exam_id: int, statement: str, points: int = 1,
                        order_index: int = 0) -> dict:
        exam = AcademicRepository.get_exam_by_id(exam_id)
        if not exam or not exam.is_active:
            raise ValueError("Examen no encontrado o inactivo")
        question = Question(exam_id=exam_id, statement=statement,
                            points=points, order_index=order_index)
        created = AcademicRepository.create_question(question)
        return {"id": created.id, "exam_id": created.exam_id,
                "statement": created.statement,
                "points": created.points,
                "order_index": created.order_index,
                "is_active": created.is_active}

    @staticmethod
    def update_question(question_id: int, data: dict) -> dict:
        q = AcademicRepository.get_question_by_id(question_id)
        if not q or not q.is_active:
            raise ValueError("Pregunta no encontrada o inactiva")
        if 'statement' in data:
            q.statement = data['statement']
        if 'points' in data:
            q.points = data['points']
        if 'order_index' in data:
            q.order_index = data['order_index']
        db.session.commit()
        return {"id": q.id, "statement": q.statement,
                "points": q.points, "is_active": q.is_active}

    @staticmethod
    def soft_delete_question(question_id: int) -> dict:
        q = AcademicRepository.get_question_by_id(question_id)
        if not q or not q.is_active:
            raise ValueError("Pregunta no encontrada o ya inactiva")
        q.is_active = False
        db.session.commit()
        return {"message": f"Pregunta {question_id} desactivada (Soft Delete)"}

    # ── OPCIONES ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_option(question_id: int, text: str,
                      order_index: int = 0) -> dict:
        q = AcademicRepository.get_question_by_id(question_id)
        if not q or not q.is_active:
            raise ValueError("Pregunta no encontrada o inactiva")
        option = Option(question_id=question_id, text=text,
                        order_index=order_index)
        created = AcademicRepository.create_option(option)
        return {"id": created.id, "question_id": created.question_id,
                "text": created.text, "order_index": created.order_index,
                "is_active": created.is_active}

    @staticmethod
    def update_option(option_id: int, data: dict) -> dict:
        o = AcademicRepository.get_option_by_id(option_id)
        if not o or not o.is_active:
            raise ValueError("Opción no encontrada o inactiva")
        if 'text' in data:
            o.text = data['text']
        if 'order_index' in data:
            o.order_index = data['order_index']
        db.session.commit()
        return {"id": o.id, "text": o.text, "is_active": o.is_active}

    @staticmethod
    def soft_delete_option(option_id: int) -> dict:
        o = AcademicRepository.get_option_by_id(option_id)
        if not o or not o.is_active:
            raise ValueError("Opción no encontrada o ya inactiva")
        o.is_active = False
        db.session.commit()
        return {"message": f"Opción {option_id} desactivada (Soft Delete)"}

    # ── CLAVE DE RESPUESTAS ───────────────────────────────────────────────────
    @staticmethod
    def set_answer_key(question_id: int, correct_option_id: int) -> dict:
        q = AcademicRepository.get_question_by_id(question_id)
        if not q or not q.is_active:
            raise ValueError("Pregunta no encontrada o inactiva")
        option = AcademicRepository.get_option_by_id(correct_option_id)
        if not option or option.question_id != question_id:
            raise ValueError("La opción no pertenece a esta pregunta")
        existing = AcademicRepository.get_answer_key_by_question(question_id)
        if existing:
            existing.correct_option_id = correct_option_id
            db.session.commit()
            return {"message": "Clave actualizada",
                    "question_id": question_id,
                    "correct_option_id": correct_option_id}
        key = AnswerKey(question_id=question_id,
                        correct_option_id=correct_option_id)
        AcademicRepository.create_answer_key(key)
        return {"message": "Clave registrada",
                "question_id": question_id,
                "correct_option_id": correct_option_id}

    # ── INTENTOS Y CALIFICACIÓN AL VUELO ──────────────────────────────────────
    @staticmethod
    def start_attempt(student_id: int, exam_id: int) -> dict:
        exam = AcademicRepository.get_exam_by_id(exam_id)
        if not exam or not exam.is_active:
            raise ValueError("Examen no encontrado o inactivo")
        previous = AcademicRepository.get_attempts_by_student_and_exam(
            student_id, exam_id)
        if len(previous) >= exam.max_attempts:
            raise ValueError(
                f"Se alcanzó el límite de {exam.max_attempts} intento(s)")
        attempt = ExamAttempt(exam_id=exam_id, student_id=student_id)
        created = AcademicRepository.create_attempt(attempt)
        return {"id": created.id, "exam_id": created.exam_id,
                "student_id": created.student_id,
                "started_at": created.started_at.isoformat(),
                "submitted_at": None}

    @staticmethod
    def submit_attempt(attempt_id: int, answers: list) -> dict:
        attempt = AcademicRepository.get_attempt_by_id(attempt_id)
        if not attempt or not attempt.is_active:
            raise ValueError("Intento no encontrado o inactivo")
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
        db.session.commit()
        return AcademicService._calculate_result(attempt_id)

    @staticmethod
    def get_attempt_result(attempt_id: int) -> dict:
        attempt = AcademicRepository.get_attempt_by_id(attempt_id)
        if not attempt or not attempt.submitted_at:
            raise ValueError("Intento no encontrado o aún no enviado")
        return AcademicService._calculate_result(attempt_id)

    @staticmethod
    def _calculate_result(attempt_id: int) -> dict:
        attempt = AcademicRepository.get_attempt_by_id(attempt_id)
        exam = AcademicRepository.get_exam_by_id(attempt.exam_id)
        student_answers = AcademicRepository.get_answers_by_attempt(attempt_id)
        student_map = {a.question_id: a.selected_option_id
                       for a in student_answers}
        answer_keys = AcademicRepository.get_answer_keys_by_exam(attempt.exam_id)
        key_map = {k.question_id: k.correct_option_id for k in answer_keys}
        total_questions = len(key_map)
        correct_count = sum(
            1 for qid, correct_opt in key_map.items()
            if student_map.get(qid) == correct_opt
        )
        score = round(
            (correct_count / total_questions) * 100
        ) if total_questions > 0 else 0
        passed = score >= exam.passing_score
        return {
            "attempt_id": attempt_id,
            "exam_id": attempt.exam_id,
            "student_id": attempt.student_id,
            "score": score,
            "passed": passed,
            "correct_answers": correct_count,
            "total_questions": total_questions,
            "passing_score": exam.passing_score,
            "submitted_at": attempt.submitted_at.isoformat()
        }