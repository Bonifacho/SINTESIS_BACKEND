from flask import Blueprint, request, jsonify
from app.core_academic.services import AcademicService
from flask_jwt_extended import jwt_required, get_jwt_identity

# Blueprint para el dominio académico
academic_bp = Blueprint('academic', __name__, url_prefix='/api/v1/academic')

@academic_bp.route('/groups', methods=['POST'])
def create_group():
    """Ruta para crear un nuevo grupo académico."""
    data = request.get_json()
    
    # Validación MVP
    if not data or 'name' not in data or 'teacher_id' not in data:
        return jsonify({"error": "Faltan datos requeridos: 'name' y 'teacher_id'"}), 400
        
    try:
        new_group = AcademicService.create_group(
            teacher_id=data['teacher_id'],
            name=data['name']
        )
        return jsonify({
            "message": "Grupo académico creado con éxito", 
            "data": new_group
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@academic_bp.route('/build-tree', methods=['POST'])
def build_tree():
    """Ruta para construir un árbol académico completo (Tema > Lección > Actividad) de un solo golpe."""
    data = request.get_json()
    
    if not data or 'group_id' not in data or 'topic' not in data:
        return jsonify({"error": "Faltan datos. Se requiere group_id y topic"}), 400
        
    try:
        result = AcademicService.build_course_tree(
            group_id=data['group_id'],
            topic_data=data['topic']
        )
        return jsonify(result), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@academic_bp.route('/progress', methods=['POST'])
def submit_progress():
    """Ruta para registrar el puntaje de un estudiante en una actividad."""
    data = request.get_json()
    
    if not data or 'student_id' not in data or 'activity_id' not in data or 'score' not in data:
        return jsonify({"error": "Faltan datos requeridos (student_id, activity_id, score)"}), 400
        
    try:
        result = AcademicService.submit_activity_score(
            student_id=data['student_id'],
            activity_id=data['activity_id'],
            score=data['score']
        )
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@academic_bp.route('/groups/<int:group_id>/course', methods=['GET'])
@jwt_required()  # <--- ¡El cadenero en acción! Solo pasan los que tengan Token
def get_course(group_id):
    """Ruta para consultar el contenido completo del curso de un grupo (Temas > Lecciones > Actividades)."""
    try:
        # Si quisieras saber el ID del usuario que está consultando, usarías:
        # current_user_id = get_jwt_identity()
        
        course_data = AcademicService.get_course_content(group_id)
        return jsonify({"message": "Curso recuperado con éxito", "data": course_data}), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@academic_bp.route('/groups/<int:group_id>', methods=['PUT'])
@jwt_required()
def update_group(group_id):
    """Ruta para actualizar el nombre de un grupo académico."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Falta el campo 'name'"}), 400
        
    try:
        updated_group = AcademicService.update_group(group_id, data['name'])
        return jsonify({"message": "Grupo actualizado", "data": updated_group}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/groups/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    """Ruta para desactivar un grupo académico (Soft Delete)."""
    try:
        result = AcademicService.soft_delete_group(group_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# ==========================================
# RUTAS DE TEMAS (TOPICS)
# ==========================================
@academic_bp.route('/topics/<int:topic_id>', methods=['PUT'])
@jwt_required()
def update_topic(topic_id):
    """Ruta para actualizar el título de un tema."""
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "Falta el campo 'title'"}), 400
    try:
        updated = AcademicService.update_topic(topic_id, data['title'])
        return jsonify({"message": "Tema actualizado", "data": updated}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/topics/<int:topic_id>', methods=['DELETE'])
@jwt_required()
def delete_topic(topic_id):
    """Ruta para desactivar un tema (Soft Delete)."""
    try:
        return jsonify(AcademicService.soft_delete_topic(topic_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# ==========================================
# RUTAS DE LECCIONES (LESSONS)
# ==========================================
@academic_bp.route('/lessons/<int:lesson_id>', methods=['PUT'])
@jwt_required()
def update_lesson(lesson_id):
    """Ruta para actualizar el título de una lección."""
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "Falta el campo 'title'"}), 400
    try:
        updated = AcademicService.update_lesson(lesson_id, data['title'])
        return jsonify({"message": "Lección actualizada", "data": updated}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/lessons/<int:lesson_id>', methods=['DELETE'])
@jwt_required()
def delete_lesson(lesson_id):
    """Ruta para desactivar una lección (Soft Delete)."""
    try:
        return jsonify(AcademicService.soft_delete_lesson(lesson_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# ==========================================
# RUTAS DE ACTIVIDADES (ACTIVITIES)
# ==========================================
@academic_bp.route('/activities/<int:activity_id>', methods=['PUT'])
@jwt_required()
def update_activity(activity_id):
    """Ruta para actualizar los datos de una actividad (título y/o configuración UI)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Faltan datos a actualizar"}), 400
    try:
        updated = AcademicService.update_activity(activity_id, data)
        return jsonify({"message": "Actividad actualizada", "data": updated}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/activities/<int:activity_id>', methods=['DELETE'])
@jwt_required()
def delete_activity(activity_id):
    """Ruta para desactivar una actividad (Soft Delete)."""
    try:
        return jsonify(AcademicService.soft_delete_activity(activity_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# ==========================================
# RUTAS DE MATRÍCULAS (ENROLLMENTS)
# ==========================================

@academic_bp.route('/enrollments', methods=['POST'])
@jwt_required()
def create_enrollment():
    """Ruta para matricular a un estudiante en un grupo académico."""
    data = request.get_json()
    if not data or 'student_id' not in data or 'group_id' not in data:
        return jsonify({"error": "Faltan datos requeridos: 'student_id' y 'group_id'"}), 400
    try:
        result = AcademicService.create_enrollment(
            student_id=data['student_id'],
            group_id=data['group_id']
        )
        return jsonify({"message": "Estudiante matriculado con éxito", "data": result}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/groups/<int:group_id>/enrollments', methods=['GET'])
@jwt_required()
def get_enrollments_by_group(group_id):
    """Ruta para consultar todos los estudiantes matriculados en un grupo."""
    try:
        enrollments = AcademicService.get_enrollments_by_group(group_id)
        return jsonify({"message": "Matrículas recuperadas con éxito", "data": enrollments}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/enrollments/<int:enrollment_id>', methods=['GET'])
@jwt_required()
def get_enrollment(enrollment_id):
    """Ruta para consultar una matrícula específica por su ID."""
    try:
        enrollment = AcademicService.get_enrollment_by_id(enrollment_id)
        return jsonify({"message": "Matrícula recuperada con éxito", "data": enrollment}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/enrollments/<int:enrollment_id>', methods=['PUT'])
@jwt_required()
def update_enrollment(enrollment_id):
    """Ruta para actualizar una matrícula (traslado de grupo)."""
    data = request.get_json()
    if not data or 'group_id' not in data:
        return jsonify({"error": "Falta el campo 'group_id' destino"}), 400
    try:
        updated = AcademicService.update_enrollment(enrollment_id, data['group_id'])
        return jsonify({"message": "Matrícula actualizada con éxito", "data": updated}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/enrollments/<int:enrollment_id>', methods=['DELETE'])
@jwt_required()
def delete_enrollment(enrollment_id):
    """Ruta para desmatricular a un estudiante (Soft Delete)."""
    try:
        result = AcademicService.soft_delete_enrollment(enrollment_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# RUTAS DE PROGRESO ESTUDIANTIL
# ==========================================

@academic_bp.route('/progress/student/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student_progress(student_id):
    """Ruta para consultar todo el progreso académico de un estudiante."""
    try:
        progress = AcademicService.get_progress_by_student(student_id)
        return jsonify({"message": "Progreso recuperado con éxito", "data": progress}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/progress/<int:progress_id>', methods=['GET'])
@jwt_required()
def get_progress(progress_id):
    """Ruta para consultar un registro de progreso específico por su ID."""
    try:
        progress = AcademicService.get_progress_by_id(progress_id)
        return jsonify({"message": "Progreso recuperado con éxito", "data": progress}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/progress/<int:progress_id>', methods=['PUT'])
@jwt_required()
def update_progress(progress_id):
    """Ruta para actualizar el puntaje de un registro de progreso."""
    data = request.get_json()
    if not data or 'score' not in data:
        return jsonify({"error": "Falta el campo 'score'"}), 400
    try:
        updated = AcademicService.update_progress(progress_id, data['score'])
        return jsonify({"message": "Progreso actualizado con éxito", "data": updated}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/progress/<int:progress_id>', methods=['DELETE'])
@jwt_required()
def delete_progress(progress_id):
    """Ruta para desactivar un registro de progreso (Soft Delete)."""
    try:
        result = AcademicService.soft_delete_progress(progress_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500