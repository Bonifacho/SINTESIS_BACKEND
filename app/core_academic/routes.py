# app/core_academic/routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core_academic.services import AcademicService
from app.utils.decorators import role_required

academic_bp = Blueprint('academic', __name__, url_prefix='/api/v1/academic')


# ── GRUPOS ────────────────────────────────────────────────────────────────────
@academic_bp.route('/groups', methods=['POST'])
@role_required('docente', 'administrador')
def create_group():
    data = request.get_json() or {}
    if 'name' not in data:
        return jsonify({"error": "Se requiere 'name'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    teacher_id = data.get('teacher_id') if ('administrador' in roles and 'teacher_id' in data) else current_user_id
    try:
        return jsonify({"message": "Grupo creado",
                        "data": AcademicService.create_group(
                            teacher_id=teacher_id,
                            name=data['name'])}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/groups', methods=['GET'])
@jwt_required()
def get_groups():
    try:
        return jsonify({"data": AcademicService.get_all_groups()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/groups/<int:group_id>', methods=['GET'])
@role_required('docente', 'administrador', 'estudiante', 'practicante')
def get_group(group_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    if not AcademicService.can_user_access_group(group_id, current_user_id, roles):
        return jsonify({"error": "Acceso denegado a este grupo"}), 403
    try:
        group_data = AcademicService.get_group(group_id)
        return jsonify(group_data), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/groups/<int:group_id>', methods=['PUT'])
@role_required('docente', 'administrador')
def update_group(group_id):
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Se requiere 'name'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Grupo actualizado",
                        "data": AcademicService.update_group(
                            group_id, data['name'], user_id=current_user_id, is_admin=is_admin)}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/groups/<int:group_id>', methods=['DELETE'])
@role_required('docente', 'administrador')
def delete_group(group_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify(AcademicService.soft_delete_group(group_id, user_id=current_user_id, is_admin=is_admin)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── MATRÍCULAS ────────────────────────────────────────────────────────────────
@academic_bp.route('/enrollments', methods=['POST'])
@role_required('docente', 'administrador')
def create_enrollment():
    data = request.get_json()
    if not data or 'student_id' not in data or 'group_id' not in data:
        return jsonify({"error": "Se requiere 'student_id' y 'group_id'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Estudiante matriculado",
                        "data": AcademicService.create_enrollment(
                            data['student_id'], data['group_id'], user_id=current_user_id, is_admin=is_admin)}), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/groups/<int:group_id>/enrollments', methods=['GET'])
@jwt_required()
def get_enrollments_by_group(group_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    if not AcademicService.can_user_access_group(group_id, current_user_id, roles):
        return jsonify({"error": "Acceso denegado a las matrículas de este grupo"}), 403
    try:
        return jsonify({"data": AcademicService.get_enrollments_by_group(
            group_id)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/enrollments/<int:enrollment_id>', methods=['GET'])
@jwt_required()
def get_enrollment(enrollment_id):
    try:
        return jsonify({"data": AcademicService.get_enrollment_by_id(
            enrollment_id)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/enrollments/<int:enrollment_id>', methods=['PUT'])
@role_required('docente', 'administrador')
def update_enrollment(enrollment_id):
    data = request.get_json()
    if not data or 'group_id' not in data:
        return jsonify({"error": "Se requiere 'group_id'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Matrícula actualizada",
                        "data": AcademicService.update_enrollment(
                            enrollment_id, data['group_id'], user_id=current_user_id, is_admin=is_admin)}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/enrollments/<int:enrollment_id>', methods=['DELETE'])
@role_required('docente', 'administrador')
def delete_enrollment(enrollment_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify(AcademicService.soft_delete_enrollment(
            enrollment_id, user_id=current_user_id, is_admin=is_admin)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── TEMAS ─────────────────────────────────────────────────────────────────────
@academic_bp.route('/topics', methods=['POST'])
@role_required('docente', 'administrador')
def create_topic():
    data = request.get_json()
    if not data or 'group_id' not in data or 'title' not in data:
        return jsonify({"error": "Se requiere 'group_id' y 'title'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Tema creado",
                        "data": AcademicService.create_topic(
                            group_id=data['group_id'],
                            title=data['title'],
                            order_index=data.get('order_index', 0),
                            user_id=current_user_id,
                            is_admin=is_admin)}), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/topics/<int:topic_id>', methods=['PUT'])
@role_required('docente', 'administrador')
def update_topic(topic_id):
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "Se requiere 'title'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Tema actualizado",
                        "data": AcademicService.update_topic(
                            topic_id, data['title'], user_id=current_user_id, is_admin=is_admin)}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/topics/<int:topic_id>', methods=['DELETE'])
@role_required('docente', 'administrador')
def delete_topic(topic_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify(AcademicService.soft_delete_topic(topic_id, user_id=current_user_id, is_admin=is_admin)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── OVAs ──────────────────────────────────────────────────────────────────────
@academic_bp.route('/ovas', methods=['POST'])
@role_required('docente', 'administrador')
def create_ova():
    data = request.get_json()
    if not data or 'topic_id' not in data or 'title' not in data:
        return jsonify({"error": "Se requiere 'topic_id' y 'title'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "OVA creado",
                        "data": AcademicService.create_ova(
                            topic_id=data['topic_id'],
                            title=data['title'],
                            description=data.get('description'),
                            order_index=data.get('order_index', 0),
                            user_id=current_user_id,
                            is_admin=is_admin)}), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/ovas/<int:ova_id>', methods=['GET'])
@jwt_required()
def get_ova(ova_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    try:
        group_id = AcademicService.get_group_id_for_ova(ova_id)
        if not AcademicService.can_user_access_group(group_id, current_user_id, roles):
            return jsonify({"error": "Acceso denegado a este OVA"}), 403
        return jsonify({"data": AcademicService.get_ova_by_id(ova_id)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/ovas/<int:ova_id>', methods=['PUT'])
@role_required('docente', 'administrador')
def update_ova(ova_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Sin datos para actualizar"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "OVA actualizado",
                        "data": AcademicService.update_ova(
                            ova_id, data, user_id=current_user_id, is_admin=is_admin)}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/ovas/<int:ova_id>', methods=['DELETE'])
@role_required('docente', 'administrador')
def delete_ova(ova_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify(AcademicService.soft_delete_ova(ova_id, user_id=current_user_id, is_admin=is_admin)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── RECURSOS ──────────────────────────────────────────────────────────────────
@academic_bp.route('/ovas/<int:ova_id>/resources', methods=['POST'])
@role_required('docente', 'administrador')
def create_resource(ova_id):
    data = request.get_json()
    if not data or 'resource_type' not in data or 'display_title' not in data:
        return jsonify({"error": "Se requiere 'resource_type' y 'display_title'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Recurso creado",
                        "data": AcademicService.create_resource(
                            ova_id=ova_id,
                            resource_type=data['resource_type'],
                            display_title=data['display_title'],
                            url=data.get('url'),
                            content=data.get('content'),
                            order_index=data.get('order_index', 0),
                            user_id=current_user_id,
                            is_admin=is_admin)}), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/resources/<int:resource_id>', methods=['PUT'])
@role_required('docente', 'administrador')
def update_resource(resource_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Sin datos para actualizar"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Recurso actualizado",
                        "data": AcademicService.update_resource(
                            resource_id, data, user_id=current_user_id, is_admin=is_admin)}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/resources/<int:resource_id>', methods=['DELETE'])
@role_required('docente', 'administrador')
def delete_resource(resource_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify(AcademicService.soft_delete_resource(resource_id, user_id=current_user_id, is_admin=is_admin)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── EXÁMENES ──────────────────────────────────────────────────────────────────
@academic_bp.route('/exams', methods=['POST'])
@role_required('docente', 'administrador')
def create_exam():
    data = request.get_json()
    if not data or 'ova_id' not in data or 'title' not in data:
        return jsonify({"error": "Se requiere 'ova_id' y 'title'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Examen creado",
                        "data": AcademicService.create_exam(
                            ova_id=data['ova_id'],
                            title=data['title'],
                            passing_score=data.get('passing_score', 60),
                            max_attempts=data.get('max_attempts', 3),
                            user_id=current_user_id,
                            is_admin=is_admin)}), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/exams/<int:exam_id>', methods=['PUT'])
@role_required('docente', 'administrador')
def update_exam(exam_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Sin datos para actualizar"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Examen actualizado",
                        "data": AcademicService.update_exam(
                            exam_id, data, user_id=current_user_id, is_admin=is_admin)}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/exams/<int:exam_id>', methods=['DELETE'])
@role_required('docente', 'administrador')
def delete_exam(exam_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify(AcademicService.soft_delete_exam(exam_id, user_id=current_user_id, is_admin=is_admin)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── PREGUNTAS ─────────────────────────────────────────────────────────────────
@academic_bp.route('/questions', methods=['POST'])
@role_required('docente', 'administrador')
def create_question():
    data = request.get_json()
    if not data or 'exam_id' not in data or 'statement' not in data:
        return jsonify({"error": "Se requiere 'exam_id' y 'statement'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Pregunta creada",
                        "data": AcademicService.create_question(
                            exam_id=data['exam_id'],
                            statement=data['statement'],
                            points=data.get('points', 1),
                            order_index=data.get('order_index', 0),
                            user_id=current_user_id,
                            is_admin=is_admin)}), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/questions/<int:question_id>', methods=['PUT'])
@role_required('docente', 'administrador')
def update_question(question_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Sin datos para actualizar"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Pregunta actualizada",
                        "data": AcademicService.update_question(
                            question_id, data, user_id=current_user_id, is_admin=is_admin)}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/questions/<int:question_id>', methods=['DELETE'])
@role_required('docente', 'administrador')
def delete_question(question_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify(AcademicService.soft_delete_question(question_id, user_id=current_user_id, is_admin=is_admin)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── OPCIONES ──────────────────────────────────────────────────────────────────
@academic_bp.route('/options', methods=['POST'])
@role_required('docente', 'administrador')
def create_option():
    data = request.get_json()
    if not data or 'question_id' not in data or 'text' not in data:
        return jsonify({"error": "Se requiere 'question_id' y 'text'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Opción creada",
                        "data": AcademicService.create_option(
                            question_id=data['question_id'],
                            text=data['text'],
                            order_index=data.get('order_index', 0),
                            user_id=current_user_id,
                            is_admin=is_admin)}), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/options/<int:option_id>', methods=['PUT'])
@role_required('docente', 'administrador')
def update_option(option_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Sin datos para actualizar"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Opción actualizada",
                        "data": AcademicService.update_option(
                            option_id, data, user_id=current_user_id, is_admin=is_admin)}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/options/<int:option_id>', methods=['DELETE'])
@role_required('docente', 'administrador')
def delete_option(option_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify(AcademicService.soft_delete_option(option_id, user_id=current_user_id, is_admin=is_admin)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── CLAVE DE RESPUESTAS ───────────────────────────────────────────────────────
@academic_bp.route('/answer-key', methods=['POST'])
@role_required('docente', 'administrador')
def set_answer_key():
    data = request.get_json()
    if not data or 'question_id' not in data or 'correct_option_id' not in data:
        return jsonify({"error": "Se requiere 'question_id' y 'correct_option_id'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify(AcademicService.set_answer_key(
            data['question_id'], data['correct_option_id'], user_id=current_user_id, is_admin=is_admin)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ── INTENTOS Y CALIFICACIÓN ───────────────────────────────────────────────────
@academic_bp.route('/attempts', methods=['POST'])
@jwt_required()
def start_attempt():
    data = request.get_json() or {}
    if 'exam_id' not in data:
        return jsonify({"error": "Se requiere 'exam_id'"}), 400
    student_id = int(get_jwt_identity())
    try:
        return jsonify({"message": "Intento iniciado",
                        "data": AcademicService.start_attempt(
                            student_id, data['exam_id'])}), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/attempts/<int:attempt_id>/submit', methods=['POST'])
@jwt_required()
def submit_attempt(attempt_id):
    data = request.get_json()
    if not data or 'answers' not in data:
        return jsonify({"error": "Se requiere la lista 'answers'"}), 400
    student_id = int(get_jwt_identity())
    try:
        return jsonify({"message": "Intento enviado",
                        "data": AcademicService.submit_attempt(
                            attempt_id, data['answers'], student_id=student_id)}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/attempts/<int:attempt_id>/result', methods=['GET'])
@jwt_required()
def get_attempt_result(attempt_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    try:
        return jsonify({"data": AcademicService.get_attempt_result(
            attempt_id, user_id=current_user_id, roles=roles)}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/attempts/<int:attempt_id>', methods=['DELETE'])
@role_required('docente', 'administrador')
def reset_attempt(attempt_id):
    """Permite al docente invalidar un intento fallido del estudiante."""
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify(AcademicService.soft_delete_attempt(
            attempt_id, user_id=current_user_id, is_admin=is_admin)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── OBSERVADORES (PRACTICANTES) ───────────────────────────────────────────────
@academic_bp.route('/groups/<int:group_id>/observers', methods=['POST'])
@role_required('docente', 'administrador')
def assign_observer(group_id):
    data = request.get_json()
    if not data or 'observer_id' not in data:
        return jsonify({"error": "Se requiere 'observer_id'"}), 400
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify({"message": "Practicante asignado al grupo",
                        "data": AcademicService.assign_observer(
                            group_id=group_id,
                            observer_id=data['observer_id'],
                            assigned_by=current_user_id,
                            is_admin=is_admin)}), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/groups/<int:group_id>/observers', methods=['GET'])
@jwt_required()
def get_observers(group_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    if not AcademicService.can_user_access_group(group_id, current_user_id, roles):
        return jsonify({"error": "Acceso denegado a los observadores de este grupo"}), 403
    try:
        return jsonify({"data": AcademicService.get_observers_by_group(
            group_id)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/observers/<int:observer_id>', methods=['DELETE'])
@role_required('docente', 'administrador')
def revoke_observer(observer_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        return jsonify(AcademicService.revoke_observer(
            observer_id, user_id=current_user_id, is_admin=is_admin)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/users/<int:user_id>/groups', methods=['GET'])
@jwt_required()
def get_user_groups(user_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    # Un usuario solo puede ver sus propios grupos a menos que sea admin
    if 'administrador' not in roles and user_id != current_user_id:
        return jsonify({"status": "error", "message": "Acceso denegado a los grupos de otro usuario"}), 403
    try:
        result = AcademicService.get_user_groups(user_id)
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@academic_bp.route('/groups/<int:group_id>/topics', methods=['GET'])
@jwt_required()
def get_group_topics(group_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    if not AcademicService.can_user_access_group(group_id, current_user_id, roles):
        return jsonify({"status": "error", "message": "Acceso denegado a los temas de este grupo"}), 403
    try:
        result = AcademicService.get_group_topics(group_id)
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@academic_bp.route('/topics/<int:topic_id>/ovas', methods=['GET'])
@jwt_required()
def get_topic_ovas(topic_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    try:
        group_id = AcademicService.get_group_id_for_topic(topic_id)
        if not AcademicService.can_user_access_group(group_id, current_user_id, roles):
            return jsonify({"status": "error", "message": "Acceso denegado a los OVAs de este grupo"}), 403
        result = AcademicService.get_ovas_by_topic(topic_id)
        return jsonify({"status": "success", "data": result}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@academic_bp.route('/exams/by-ova/<int:ova_id>', methods=['GET'])
@jwt_required()
def get_exam_by_ova_full(ova_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    try:
        group_id = AcademicService.get_group_id_for_ova(ova_id)
        if not AcademicService.can_user_access_group(group_id, current_user_id, roles):
            return jsonify({"status": "error", "message": "Acceso denegado al examen de este grupo"}), 403
        result = AcademicService.get_exam_by_ova_full(ova_id)
        return jsonify({"status": "success", "data": result}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@academic_bp.route('/exams/by-ova/<int:ova_id>/teacher', methods=['GET'])
@role_required('docente', 'administrador')
def get_exam_by_ova_teacher(ova_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    is_admin = 'administrador' in claims.get('roles', [])
    try:
        result = AcademicService.get_exam_by_ova_teacher(
            ova_id, user_id=current_user_id, is_admin=is_admin)
        return jsonify({"status": "success", "data": result}), 200
    except PermissionError as e:
        return jsonify({"status": "error", "message": str(e)}), 403
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@academic_bp.route('/students/<int:student_id>/attempts', methods=['GET'])
@jwt_required()
def get_student_attempts(student_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    if 'estudiante' in roles and not any(r in roles for r in ['administrador', 'docente', 'practicante']):
        if student_id != current_user_id:
            return jsonify({"status": "error", "message": "Acceso denegado: no puedes consultar intentos de otros estudiantes"}), 403
    try:
        result = AcademicService.get_attempts_by_student(student_id)
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@academic_bp.route('/groups/<int:group_id>/attempts', methods=['GET'])
@jwt_required()
def get_group_attempts(group_id):
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    if not AcademicService.can_user_access_group(group_id, current_user_id, roles):
        return jsonify({"status": "error", "message": "Acceso denegado a los intentos de este grupo"}), 403
    try:
        result = AcademicService.get_attempts_by_group(group_id)
        return jsonify({"status": "success", "data": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ── PROGRESO (TRACKING SILENCIOSO) ────────────────────────────────────────
@academic_bp.route('/progress', methods=['POST'])
@jwt_required()
def register_progress():
    data = request.get_json() or {}
    if 'ova_id' not in data or 'action' not in data:
        return jsonify({"error": "Se requiere 'ova_id' y 'action'"}), 400
    user_id = int(get_jwt_identity())
    try:
        result = AcademicService.register_progress(
            user_id=user_id,
            ova_id=data['ova_id'],
            action=data['action'],
            topic_name=data.get('topic_name'),
            resource_name=data.get('resource_name'))
        return jsonify({"message": "Progreso registrado",
                        "data": {"id": result["id"]}}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@academic_bp.route('/groups/<int:group_id>/activity', methods=['GET'])
@role_required('docente', 'administrador', 'practicante')
def get_group_activity(group_id):
    """Historial de tracking silencioso del grupo. Solo para docente/practicante/admin asignados."""
    current_user_id = int(get_jwt_identity())
    claims = get_jwt() or {}
    roles = claims.get('roles', [])
    if not AcademicService.can_user_access_group(group_id, current_user_id, roles):
        return jsonify({"error": "Acceso denegado a la actividad de este grupo"}), 403
    try:
        result = AcademicService.get_group_activity(group_id)
        return jsonify({"data": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
