from app.extensions import db
from app.core_academic.models import Group, Topic, Lesson, Activity, Enrollment, StudentProgress

class AcademicRepository:
    @staticmethod
    def create_group(group: Group) -> Group:
        db.session.add(group)
        db.session.commit()
        return group
    
    @staticmethod
    def get_group_by_id(group_id: int) -> Group:
        return db.session.query(Group).filter_by(id=group_id).first()
    
    @staticmethod
    def get_topic_by_id(topic_id: int) -> Topic:
        return db.session.query(Topic).filter_by(id=topic_id).first()

    @staticmethod
    def get_lesson_by_id(lesson_id: int) -> Lesson:
        return db.session.query(Lesson).filter_by(id=lesson_id).first()

    @staticmethod
    def get_activity_by_id(activity_id: int) -> Activity:
        return db.session.query(Activity).filter_by(id=activity_id).first()

    # ==========================================
    # REPOSITORIO DE MATRÍCULAS (ENROLLMENTS)
    # ==========================================
    @staticmethod
    def create_enrollment(enrollment: Enrollment) -> Enrollment:
        """Persiste una nueva matrícula en la base de datos."""
        db.session.add(enrollment)
        db.session.commit()
        return enrollment

    @staticmethod
    def get_enrollment_by_id(enrollment_id: int) -> Enrollment:
        """Obtiene una matrícula por su ID."""
        return db.session.query(Enrollment).filter_by(id=enrollment_id).first()

    @staticmethod
    def get_enrollments_by_group(group_id: int):
        """Obtiene todas las matrículas activas de un grupo."""
        return db.session.query(Enrollment).filter_by(group_id=group_id, is_active=True).all()

    @staticmethod
    def get_enrollment_by_student_and_group(student_id: int, group_id: int) -> Enrollment:
        """Busca si un estudiante ya está matriculado en un grupo específico."""
        return db.session.query(Enrollment).filter_by(
            student_id=student_id, group_id=group_id, is_active=True
        ).first()

    # ==========================================
    # REPOSITORIO DE PROGRESO ESTUDIANTIL
    # ==========================================
    @staticmethod
    def get_progress_by_id(progress_id: int) -> StudentProgress:
        """Obtiene un registro de progreso por su ID."""
        return db.session.query(StudentProgress).filter_by(id=progress_id).first()

    @staticmethod
    def get_progress_by_student(student_id: int):
        """Obtiene todo el progreso activo de un estudiante."""
        return db.session.query(StudentProgress).filter_by(student_id=student_id, is_active=True).all()

    @staticmethod
    def get_progress_by_activity(activity_id: int):
        """Obtiene todo el progreso activo de una actividad."""
        return db.session.query(StudentProgress).filter_by(activity_id=activity_id, is_active=True).all()