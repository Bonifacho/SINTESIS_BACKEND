from app.core_academic.models import Group, Topic, Lesson, Activity
from app.core_academic.repositories import AcademicRepository
from app.core_academic.models import Group, Topic, Lesson, Activity, StudentProgress
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