# app/core_academic/routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.core_academic.services import AcademicService

academic_bp = Blueprint('academic', __name__, url_prefix='/api/v1/academic')


# ── GRUPOS ────────────────────────────────────────────────────────────────────
@academic_bp.route('/groups', methods=['POST'])
@jwt_required()
def create_group():
    data = request.get_json()
    if not data or 'name' not in data or 'teacher_id' not in data:
        return jsonify({"error": "Se requiere 'name' y 'teacher_id'"}), 400
    try:
        return jsonify({"message": "Grupo creado",
                        "data": AcademicService.create_group(
                            teacher_id=data['teacher_id'],
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

@academic_bp.route('/groups/<int:group_id>', methods=['PUT'])
@jwt_required()
def update_group(group_id):
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Se requiere 'name'"}), 400
    try:
        return jsonify({"message": "Grupo actualizado",
                        "data": AcademicService.update_group(
                            group_id, data['name'])}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/groups/<int:group_id>', methods=['DELETE'])
@jwt_required()
def delete_group(group_id):
    try:
        return jsonify(AcademicService.soft_delete_group(group_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── MATRÍCULAS ────────────────────────────────────────────────────────────────
@academic_bp.route('/enrollments', methods=['POST'])
@jwt_required()
def create_enrollment():
    data = request.get_json()
    if not data or 'student_id' not in data or 'group_id' not in data:
        return jsonify({"error": "Se requiere 'student_id' y 'group_id'"}), 400
    try:
        return jsonify({"message": "Estudiante matriculado",
                        "data": AcademicService.create_enrollment(
                            data['student_id'], data['group_id'])}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@academic_bp.route('/groups/<int:group_id>/enrollments', methods=['GET'])
@jwt_required()
def get_enrollments_by_group(group_id):
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
@jwt_required()
def update_enrollment(enrollment_id):
    data = request.get_json()
    if not data or 'group_id' not in data:
        return jsonify({"error": "Se requiere 'group_id'"}), 400
    try:
        return jsonify({"message": "Matrícula actualizada",
                        "data": AcademicService.update_enrollment(
                            enrollment_id, data['group_id'])}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/enrollments/<int:enrollment_id>', methods=['DELETE'])
@jwt_required()
def delete_enrollment(enrollment_id):
    try:
        return jsonify(AcademicService.soft_delete_enrollment(
            enrollment_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── TEMAS ─────────────────────────────────────────────────────────────────────
@academic_bp.route('/topics', methods=['POST'])
@jwt_required()
def create_topic():
    data = request.get_json()
    if not data or 'group_id' not in data or 'title' not in data:
        return jsonify({"error": "Se requiere 'group_id' y 'title'"}), 400
    try:
        return jsonify({"message": "Tema creado",
                        "data": AcademicService.create_topic(
                            group_id=data['group_id'],
                            title=data['title'],
                            order_index=data.get('order_index', 0))}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/topics/<int:topic_id>', methods=['PUT'])
@jwt_required()
def update_topic(topic_id):
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({"error": "Se requiere 'title'"}), 400
    try:
        return jsonify({"message": "Tema actualizado",
                        "data": AcademicService.update_topic(
                            topic_id, data['title'])}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/topics/<int:topic_id>', methods=['DELETE'])
@jwt_required()
def delete_topic(topic_id):
    try:
        return jsonify(AcademicService.soft_delete_topic(topic_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── OVAs ──────────────────────────────────────────────────────────────────────
@academic_bp.route('/ovas', methods=['POST'])
@jwt_required()
def create_ova():
    data = request.get_json()
    if not data or 'topic_id' not in data or 'title' not in data:
        return jsonify({"error": "Se requiere 'topic_id' y 'title'"}), 400
    try:
        return jsonify({"message": "OVA creado",
                        "data": AcademicService.create_ova(
                            topic_id=data['topic_id'],
                            title=data['title'],
                            description=data.get('description'),
                            order_index=data.get('order_index', 0))}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/ovas/<int:ova_id>', methods=['GET'])
@jwt_required()
def get_ova(ova_id):
    try:
        return jsonify({"data": AcademicService.get_ova_by_id(ova_id)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/ovas/<int:ova_id>', methods=['PUT'])
@jwt_required()
def update_ova(ova_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Sin datos para actualizar"}), 400
    try:
        return jsonify({"message": "OVA actualizado",
                        "data": AcademicService.update_ova(
                            ova_id, data)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/ovas/<int:ova_id>', methods=['DELETE'])
@jwt_required()
def delete_ova(ova_id):
    try:
        return jsonify(AcademicService.soft_delete_ova(ova_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── RECURSOS ──────────────────────────────────────────────────────────────────
@academic_bp.route('/ovas/<int:ova_id>/resources', methods=['POST'])
@jwt_required()
def create_resource(ova_id):
    data = request.get_json()
    if not data or 'resource_type' not in data or 'display_title' not in data:
        return jsonify({"error": "Se requiere 'resource_type' y 'display_title'"}), 400
    try:
        return jsonify({"message": "Recurso creado",
                        "data": AcademicService.create_resource(
                            ova_id=ova_id,
                            resource_type=data['resource_type'],
                            display_title=data['display_title'],
                            url=data.get('url'),
                            content=data.get('content'),
                            order_index=data.get('order_index', 0))}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/resources/<int:resource_id>', methods=['PUT'])
@jwt_required()
def update_resource(resource_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Sin datos para actualizar"}), 400
    try:
        return jsonify({"message": "Recurso actualizado",
                        "data": AcademicService.update_resource(
                            resource_id, data)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/resources/<int:resource_id>', methods=['DELETE'])
@jwt_required()
def delete_resource(resource_id):
    try:
        return jsonify(AcademicService.soft_delete_resource(resource_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── EXÁMENES ──────────────────────────────────────────────────────────────────
@academic_bp.route('/exams', methods=['POST'])
@jwt_required()
def create_exam():
    data = request.get_json()
    if not data or 'ova_id' not in data or 'title' not in data:
        return jsonify({"error": "Se requiere 'ova_id' y 'title'"}), 400
    try:
        return jsonify({"message": "Examen creado",
                        "data": AcademicService.create_exam(
                            ova_id=data['ova_id'],
                            title=data['title'],
                            passing_score=data.get('passing_score', 60),
                            max_attempts=data.get('max_attempts', 3))}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/exams/<int:exam_id>', methods=['PUT'])
@jwt_required()
def update_exam(exam_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Sin datos para actualizar"}), 400
    try:
        return jsonify({"message": "Examen actualizado",
                        "data": AcademicService.update_exam(
                            exam_id, data)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/exams/<int:exam_id>', methods=['DELETE'])
@jwt_required()
def delete_exam(exam_id):
    try:
        return jsonify(AcademicService.soft_delete_exam(exam_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── PREGUNTAS ─────────────────────────────────────────────────────────────────
@academic_bp.route('/questions', methods=['POST'])
@jwt_required()
def create_question():
    data = request.get_json()
    if not data or 'exam_id' not in data or 'statement' not in data:
        return jsonify({"error": "Se requiere 'exam_id' y 'statement'"}), 400
    try:
        return jsonify({"message": "Pregunta creada",
                        "data": AcademicService.create_question(
                            exam_id=data['exam_id'],
                            statement=data['statement'],
                            points=data.get('points', 1),
                            order_index=data.get('order_index', 0))}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/questions/<int:question_id>', methods=['PUT'])
@jwt_required()
def update_question(question_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Sin datos para actualizar"}), 400
    try:
        return jsonify({"message": "Pregunta actualizada",
                        "data": AcademicService.update_question(
                            question_id, data)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/questions/<int:question_id>', methods=['DELETE'])
@jwt_required()
def delete_question(question_id):
    try:
        return jsonify(AcademicService.soft_delete_question(question_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── OPCIONES ──────────────────────────────────────────────────────────────────
@academic_bp.route('/options', methods=['POST'])
@jwt_required()
def create_option():
    data = request.get_json()
    if not data or 'question_id' not in data or 'text' not in data:
        return jsonify({"error": "Se requiere 'question_id' y 'text'"}), 400
    try:
        return jsonify({"message": "Opción creada",
                        "data": AcademicService.create_option(
                            question_id=data['question_id'],
                            text=data['text'],
                            order_index=data.get('order_index', 0))}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/options/<int:option_id>', methods=['PUT'])
@jwt_required()
def update_option(option_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Sin datos para actualizar"}), 400
    try:
        return jsonify({"message": "Opción actualizada",
                        "data": AcademicService.update_option(
                            option_id, data)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@academic_bp.route('/options/<int:option_id>', methods=['DELETE'])
@jwt_required()
def delete_option(option_id):
    try:
        return jsonify(AcademicService.soft_delete_option(option_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── CLAVE DE RESPUESTAS ───────────────────────────────────────────────────────
@academic_bp.route('/answer-key', methods=['POST'])
@jwt_required()
def set_answer_key():
    data = request.get_json()
    if not data or 'question_id' not in data or 'correct_option_id' not in data:
        return jsonify({"error": "Se requiere 'question_id' y 'correct_option_id'"}), 400
    try:
        return jsonify(AcademicService.set_answer_key(
            data['question_id'], data['correct_option_id'])), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ── INTENTOS Y CALIFICACIÓN ───────────────────────────────────────────────────
@academic_bp.route('/attempts', methods=['POST'])
@jwt_required()
def start_attempt():
    data = request.get_json()
    if not data or 'student_id' not in data or 'exam_id' not in data:
        return jsonify({"error": "Se requiere 'student_id' y 'exam_id'"}), 400
    try:
        return jsonify({"message": "Intento iniciado",
                        "data": AcademicService.start_attempt(
                            data['student_id'], data['exam_id'])}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/attempts/<int:attempt_id>/submit', methods=['POST'])
@jwt_required()
def submit_attempt(attempt_id):
    data = request.get_json()
    if not data or 'answers' not in data:
        return jsonify({"error": "Se requiere la lista 'answers'"}), 400
    try:
        return jsonify({"message": "Intento enviado",
                        "data": AcademicService.submit_attempt(
                            attempt_id, data['answers'])}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@academic_bp.route('/attempts/<int:attempt_id>/result', methods=['GET'])
@jwt_required()
def get_attempt_result(attempt_id):
    try:
        return jsonify({"data": AcademicService.get_attempt_result(
            attempt_id)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404