# app/core_academic/repositories.py
from app.extensions import db
from app.core_academic.models import (
    Group, Enrollment, Topic,
    OVA, OVAResource,
    Exam, Question, Option, AnswerKey,
    ExamAttempt, AttemptAnswer,
    GroupObserver
)


class AcademicRepository:

    # ── GRUPOS ────────────────────────────────────────────────────────────────
    @staticmethod
    def create_group(group: Group) -> Group:
        db.session.add(group)
        db.session.commit()
        return group

    @staticmethod
    def get_group_by_id(group_id: int) -> Group:
        return db.session.query(Group).filter_by(id=group_id).first()

    @staticmethod
    def get_all_groups():
        return db.session.query(Group).filter_by(is_active=True).all()

    # ── MATRÍCULAS ────────────────────────────────────────────────────────────
    @staticmethod
    def create_enrollment(enrollment: Enrollment) -> Enrollment:
        db.session.add(enrollment)
        db.session.commit()
        return enrollment

    @staticmethod
    def get_enrollment_by_id(enrollment_id: int) -> Enrollment:
        return db.session.query(Enrollment).filter_by(id=enrollment_id).first()

    @staticmethod
    def get_enrollments_by_group(group_id: int):
        return db.session.query(Enrollment).filter_by(
            group_id=group_id, is_active=True
        ).all()

    @staticmethod
    def get_enrollment_by_student_and_group(student_id: int, group_id: int):
        return db.session.query(Enrollment).filter_by(
            student_id=student_id, group_id=group_id, is_active=True
        ).first()

    # ── TEMAS ─────────────────────────────────────────────────────────────────
    @staticmethod
    def create_topic(topic: Topic) -> Topic:
        db.session.add(topic)
        db.session.commit()
        return topic

    @staticmethod
    def get_topic_by_id(topic_id: int) -> Topic:
        return db.session.query(Topic).filter_by(id=topic_id).first()

    # ── OVAs ──────────────────────────────────────────────────────────────────
    @staticmethod
    def create_ova(ova: OVA) -> OVA:
        db.session.add(ova)
        db.session.commit()
        return ova

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
    def create_resource(resource: OVAResource) -> OVAResource:
        db.session.add(resource)
        db.session.commit()
        return resource

    @staticmethod
    def get_resource_by_id(resource_id: int) -> OVAResource:
        return db.session.query(OVAResource).filter_by(id=resource_id).first()

    @staticmethod
    def get_resources_by_ova(ova_id: int):
        return db.session.query(OVAResource).filter_by(
            ova_id=ova_id, is_active=True
        ).order_by(OVAResource.order_index).all()

    # ── EXÁMENES ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_exam(exam: Exam) -> Exam:
        db.session.add(exam)
        db.session.commit()
        return exam

    @staticmethod
    def get_exam_by_id(exam_id: int) -> Exam:
        return db.session.query(Exam).filter_by(id=exam_id).first()

    @staticmethod
    def get_exam_by_ova(ova_id: int) -> Exam:
        return db.session.query(Exam).filter_by(
            ova_id=ova_id, is_active=True
        ).first()

    # ── PREGUNTAS ─────────────────────────────────────────────────────────────
    @staticmethod
    def create_question(question: Question) -> Question:
        db.session.add(question)
        db.session.commit()
        return question

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
    def create_option(option: Option) -> Option:
        db.session.add(option)
        db.session.commit()
        return option

    @staticmethod
    def get_option_by_id(option_id: int) -> Option:
        return db.session.query(Option).filter_by(id=option_id).first()

    @staticmethod
    def get_options_by_question(question_id: int):
        return db.session.query(Option).filter_by(
            question_id=question_id, is_active=True
        ).order_by(Option.order_index).all()

    # ── CLAVE DE RESPUESTAS ───────────────────────────────────────────────────
    @staticmethod
    def create_answer_key(answer_key: AnswerKey) -> AnswerKey:
        db.session.add(answer_key)
        db.session.commit()
        return answer_key

    @staticmethod
    def get_answer_key_by_question(question_id: int) -> AnswerKey:
        return db.session.query(AnswerKey).filter_by(
            question_id=question_id, is_active=True
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
    def create_attempt(attempt: ExamAttempt) -> ExamAttempt:
        db.session.add(attempt)
        db.session.commit()
        return attempt

    @staticmethod
    def get_attempt_by_id(attempt_id: int) -> ExamAttempt:
        return db.session.query(ExamAttempt).filter_by(id=attempt_id).first()

    @staticmethod
    def get_attempts_by_student_and_exam(student_id: int, exam_id: int):
        return db.session.query(ExamAttempt).filter_by(
            student_id=student_id, exam_id=exam_id, is_active=True
        ).all()

    # ── RESPUESTAS DEL INTENTO ────────────────────────────────────────────────
    @staticmethod
    def create_attempt_answer(answer: AttemptAnswer) -> AttemptAnswer:
        db.session.add(answer)
        db.session.commit()
        return answer

    @staticmethod
    def get_answers_by_attempt(attempt_id: int):
        return db.session.query(AttemptAnswer).filter_by(
            attempt_id=attempt_id, is_active=True
        ).all()
        
# ── OBSERVADORES (PRACTICANTES) ───────────────────────────────────────────
    @staticmethod
    def create_observer(observer: GroupObserver) -> GroupObserver:
        db.session.add(observer)
        db.session.commit()
        return observer

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
    def get_observers_by_group(group_id: int):
        return db.session.query(GroupObserver).filter_by(
            group_id=group_id, is_active=True).all()