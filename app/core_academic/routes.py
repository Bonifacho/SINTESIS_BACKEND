from flask import Blueprint, request, jsonify
from app.core_academic.services import AcademicService
from flask_jwt_extended import jwt_required, get_jwt_identity

# Blueprint para el dominio académico
academic_bp = Blueprint('academic', __name__, url_prefix='/api/v1/academic')

@academic_bp.route('/groups', methods=['POST'])
def create_group():
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
    try:
        result = AcademicService.soft_delete_group(group_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
