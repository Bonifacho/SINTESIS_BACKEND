from app.core_academic.models import Group, Topic, Lesson, Activity, StudentProgress, Enrollment
from app.core_academic.repositories import AcademicRepository
from app.extensions import db

class AcademicService:
    
    @staticmethod
    def create_group(teacher_id: int, name: str) -> dict:
        new_group = Group(name=name, teacher_id=teacher_id)
        created_group = AcademicRepository.create_group(new_group)
        return {
            "id": created_group.id,
            "name": created_group.name,
            "teacher_id": created_group.teacher_id,
            "created_at": created_group.created_at.isoformat()
        }

    # Fíjate que esta línea está a la misma altura (indentación) que la de arriba
    @staticmethod
    def build_course_tree(group_id: int, topic_data: dict) -> dict:
        """Crea un Tema, una Lección y una Actividad de un solo golpe (Modo MVP)"""
        
        # 1. Crear el Tema
        topic = Topic(title=topic_data['title'], group_id=group_id, order_index=1)
        db.session.add(topic)
        db.session.flush()

        # 2. Crear la Lección
        lesson_data = topic_data['lesson']
        lesson = Lesson(title=lesson_data['title'], topic_id=topic.id, order_index=1)
        db.session.add(lesson)
        db.session.flush()

        # 3. Crear la Actividad (EL CORAZÓN DEL AGNOSTICISMO)
        activity_data = lesson_data['activity']
        activity = Activity(
            title=activity_data['title'],
            lesson_id=lesson.id,
            ui_config=activity_data['ui_config'], 
            passing_score=activity_data.get('passing_score', 80),
            order_index=1
        )
        db.session.add(activity)
        
        db.session.commit()

        return {
            "message": "Árbol académico construido con éxito",
            "topic_id": topic.id,
            "lesson_id": lesson.id,
            "activity_id": activity.id
        }
        
    @staticmethod
    def submit_activity_score(student_id: int, activity_id: int, score: int) -> dict:
        """Recibe el puntaje de Android, evalúa si aprueba y guarda el progreso"""
        
        # 1. Buscar la actividad para saber cuál era la nota mínima (passing_score)
        activity = db.session.query(Activity).get(activity_id)
        if not activity:
            raise ValueError("Actividad no encontrada")

        # 2. Lógica Duolingo: ¿Aprobó?
        passed = score >= activity.passing_score

        # 3. Guardar el intento en la base de datos
        progress = StudentProgress(
            student_id=student_id,
            activity_id=activity_id,
            score=score,
            passed=passed
        )
        db.session.add(progress)
        db.session.commit()

        return {
            "message": "Progreso guardado con éxito",
            "score": score,
            "passed": passed,
            "unlocked_next": passed # Si aprobó, la app desbloquea el siguiente nivel
        }
        
    @staticmethod
    def get_course_content(group_id: int) -> dict:
        group = AcademicRepository.get_group_by_id(group_id)
        if not group:
            raise ValueError("Grupo no encontrado")

        # Armamos el árbol iterando sobre las relaciones de SQLAlchemy
        course_data = []
        for topic in group.topics:
            topic_data = {
                "id": topic.id,
                "title": topic.title,
                "lessons": []
            }
            for lesson in topic.lessons:
                lesson_data = {
                    "id": lesson.id,
                    "title": lesson.title,
                    "activities": []
                }
                for activity in lesson.activities:
                    activity_data = {
                        "id": activity.id,
                        "title": activity.title,
                        "passing_score": activity.passing_score,
                        "ui_config": activity.ui_config  # <--- El diseño agnóstico
                    }
                    lesson_data["activities"].append(activity_data)
                topic_data["lessons"].append(lesson_data)
            course_data.append(topic_data)

        return {
            "group_id": group.id,
            "group_name": group.name,
            "course_tree": course_data
        }
        
        
    @staticmethod
    def update_group(group_id: int, new_name: str) -> dict:
        """Actualiza (PUT) el nombre de un grupo"""
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o inactivo")
            
        group.name = new_name
        db.session.commit()
        
        return {"id": group.id, "name": group.name, "is_active": group.is_active}

    @staticmethod
    def soft_delete_group(group_id: int) -> dict:
        """Borrado lógico (DELETE) de un grupo"""
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o ya estaba inactivo")
            
        group.is_active = False  # <--- AQUÍ OCURRE LA MAGIA DEL SOFT DELETE
        db.session.commit()
        
        return {"message": f"Grupo {group_id} desactivado correctamente (Soft Delete)"}
    
    # --- CRUD TEMAS (TOPICS) ---
    @staticmethod
    def update_topic(topic_id: int, new_title: str) -> dict:
        topic = AcademicRepository.get_topic_by_id(topic_id)
        if not topic or not topic.is_active:
            raise ValueError("Tema no encontrado o inactivo")
        topic.title = new_title
        db.session.commit()
        return {"id": topic.id, "title": topic.title, "is_active": topic.is_active}

    @staticmethod
    def soft_delete_topic(topic_id: int) -> dict:
        topic = AcademicRepository.get_topic_by_id(topic_id)
        if not topic or not topic.is_active:
            raise ValueError("Tema no encontrado o ya estaba inactivo")
        topic.is_active = False
        db.session.commit()
        return {"message": f"Tema {topic_id} desactivado (Soft Delete)"}

    # --- CRUD LECCIONES (LESSONS) ---
    @staticmethod
    def update_lesson(lesson_id: int, new_title: str) -> dict:
        lesson = AcademicRepository.get_lesson_by_id(lesson_id)
        if not lesson or not lesson.is_active:
            raise ValueError("Lección no encontrada o inactiva")
        lesson.title = new_title
        db.session.commit()
        return {"id": lesson.id, "title": lesson.title, "is_active": lesson.is_active}

    @staticmethod
    def soft_delete_lesson(lesson_id: int) -> dict:
        lesson = AcademicRepository.get_lesson_by_id(lesson_id)
        if not lesson or not lesson.is_active:
            raise ValueError("Lección no encontrada o ya estaba inactiva")
        lesson.is_active = False
        db.session.commit()
        return {"message": f"Lección {lesson_id} desactivada (Soft Delete)"}

    # --- CRUD ACTIVIDADES (ACTIVITIES) ---
    @staticmethod
    def update_activity(activity_id: int, update_data: dict) -> dict:
        activity = AcademicRepository.get_activity_by_id(activity_id)
        if not activity or not activity.is_active:
            raise ValueError("Actividad no encontrada o inactiva")
        # En la actividad podemos actualizar el título o el diseño (ui_config)
        if 'title' in update_data:
            activity.title = update_data['title']
        if 'ui_config' in update_data:
            activity.ui_config = update_data['ui_config']
        db.session.commit()
        return {"id": activity.id, "title": activity.title, "is_active": activity.is_active}

    @staticmethod
    def soft_delete_activity(activity_id: int) -> dict:
        activity = AcademicRepository.get_activity_by_id(activity_id)
        if not activity or not activity.is_active:
            raise ValueError("Actividad no encontrada o ya estaba inactiva")
        activity.is_active = False
        db.session.commit()
        return {"message": f"Actividad {activity_id} desactivada (Soft Delete)"}

    # ==========================================
    # CRUD DE MATRÍCULAS (ENROLLMENTS)
    # ==========================================
    @staticmethod
    def create_enrollment(student_id: int, group_id: int) -> dict:
        """Matricula a un estudiante en un grupo académico."""
        # Verificar que el grupo exista y esté activo
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o inactivo")
        # Verificar que no esté ya matriculado
        existing = AcademicRepository.get_enrollment_by_student_and_group(student_id, group_id)
        if existing:
            raise ValueError("El estudiante ya está matriculado en este grupo")
        enrollment = Enrollment(student_id=student_id, group_id=group_id)
        created = AcademicRepository.create_enrollment(enrollment)
        return {
            "id": created.id,
            "student_id": created.student_id,
            "group_id": created.group_id,
            "enrolled_at": created.enrolled_at.isoformat(),
            "is_active": created.is_active
        }

    @staticmethod
    def get_enrollments_by_group(group_id: int) -> list:
        """Obtiene la lista de estudiantes matriculados en un grupo."""
        group = AcademicRepository.get_group_by_id(group_id)
        if not group or not group.is_active:
            raise ValueError("Grupo no encontrado o inactivo")
        enrollments = AcademicRepository.get_enrollments_by_group(group_id)
        return [{
            "id": e.id,
            "student_id": e.student_id,
            "group_id": e.group_id,
            "enrolled_at": e.enrolled_at.isoformat(),
            "is_active": e.is_active
        } for e in enrollments]

    @staticmethod
    def get_enrollment_by_id(enrollment_id: int) -> dict:
        """Obtiene una matrícula específica por su ID."""
        enrollment = AcademicRepository.get_enrollment_by_id(enrollment_id)
        if not enrollment or not enrollment.is_active:
            raise ValueError("Matrícula no encontrada o inactiva")
        return {
            "id": enrollment.id,
            "student_id": enrollment.student_id,
            "group_id": enrollment.group_id,
            "enrolled_at": enrollment.enrolled_at.isoformat(),
            "is_active": enrollment.is_active
        }

    @staticmethod
    def update_enrollment(enrollment_id: int, new_group_id: int) -> dict:
        """Actualiza la matrícula (traslado de grupo)."""
        enrollment = AcademicRepository.get_enrollment_by_id(enrollment_id)
        if not enrollment or not enrollment.is_active:
            raise ValueError("Matrícula no encontrada o inactiva")
        # Verificar que el nuevo grupo exista
        new_group = AcademicRepository.get_group_by_id(new_group_id)
        if not new_group or not new_group.is_active:
            raise ValueError("Grupo destino no encontrado o inactivo")
        enrollment.group_id = new_group_id
        db.session.commit()
        return {
            "id": enrollment.id,
            "student_id": enrollment.student_id,
            "group_id": enrollment.group_id,
            "enrolled_at": enrollment.enrolled_at.isoformat(),
            "is_active": enrollment.is_active
        }

    @staticmethod
    def soft_delete_enrollment(enrollment_id: int) -> dict:
        """Desmatricular estudiante (Soft Delete)."""
        enrollment = AcademicRepository.get_enrollment_by_id(enrollment_id)
        if not enrollment or not enrollment.is_active:
            raise ValueError("Matrícula no encontrada o ya estaba inactiva")
        enrollment.is_active = False
        db.session.commit()
        return {"message": f"Matrícula {enrollment_id} desactivada (Soft Delete)"}

    # ==========================================
    # CRUD DE PROGRESO ESTUDIANTIL
    # ==========================================
    @staticmethod
    def get_progress_by_student(student_id: int) -> list:
        """Obtiene todo el progreso académico de un estudiante."""
        progress_list = AcademicRepository.get_progress_by_student(student_id)
        return [{
            "id": p.id,
            "student_id": p.student_id,
            "activity_id": p.activity_id,
            "score": p.score,
            "passed": p.passed,
            "completed_at": p.completed_at.isoformat(),
            "is_active": p.is_active
        } for p in progress_list]

    @staticmethod
    def get_progress_by_id(progress_id: int) -> dict:
        """Obtiene un registro de progreso específico por su ID."""
        progress = AcademicRepository.get_progress_by_id(progress_id)
        if not progress or not progress.is_active:
            raise ValueError("Registro de progreso no encontrado o inactivo")
        return {
            "id": progress.id,
            "student_id": progress.student_id,
            "activity_id": progress.activity_id,
            "score": progress.score,
            "passed": progress.passed,
            "completed_at": progress.completed_at.isoformat(),
            "is_active": progress.is_active
        }

    @staticmethod
    def update_progress(progress_id: int, new_score: int) -> dict:
        """Actualiza el puntaje de un registro de progreso y recalcula aprobación."""
        progress = AcademicRepository.get_progress_by_id(progress_id)
        if not progress or not progress.is_active:
            raise ValueError("Registro de progreso no encontrado o inactivo")
        # Obtener la actividad asociada para recalcular si aprueba
        activity = AcademicRepository.get_activity_by_id(progress.activity_id)
        progress.score = new_score
        progress.passed = new_score >= activity.passing_score
        db.session.commit()
        return {
            "id": progress.id,
            "student_id": progress.student_id,
            "activity_id": progress.activity_id,
            "score": progress.score,
            "passed": progress.passed,
            "is_active": progress.is_active
        }

    @staticmethod
    def soft_delete_progress(progress_id: int) -> dict:
        """Desactiva un registro de progreso (Soft Delete)."""
        progress = AcademicRepository.get_progress_by_id(progress_id)
        if not progress or not progress.is_active:
            raise ValueError("Registro de progreso no encontrado o ya estaba inactivo")
        progress.is_active = False
        db.session.commit()
        return {"message": f"Progreso {progress_id} desactivado (Soft Delete)"}