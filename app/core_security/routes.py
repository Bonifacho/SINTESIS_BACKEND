# app/core_security/routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required,
    get_jwt_identity, get_jwt
)
from datetime import datetime, timezone, timedelta
from app.core_security.services import SecurityService
from app.core_security.repositories import SecurityRepository

security_bp = Blueprint('security', __name__, url_prefix='/api/v1/security')


# ── REGISTRO ──────────────────────────────────────────────────────────────────
@security_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    required = ['first_name', 'last_name', 'document_id',
                 'username', 'password']
    if not data or not all(k in data for k in required):
        return jsonify({"error": f"Se requieren: {required}"}), 400
    try:
        # El rol "estudiante" se asigna internamente en el servicio.
        # Cualquier role_name enviado por el cliente es IGNORADO.
        result = SecurityService.register_user(
            first_name=data['first_name'],
            last_name=data['last_name'],
            document_id=data['document_id'],
            username=data['username'],
            password=data['password']
        )
        return jsonify({"message": "Usuario registrado exitosamente",
                        "data": result}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── LOGIN ─────────────────────────────────────────────────────────────────────
@security_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Se requiere 'username' y 'password'"}), 400
    try:
        user_data = SecurityService.login_user(
            username=data['username'],
            password=data['password']
        )
        # El JWT lleva el user_id como identity y los roles en claims
        access_token = create_access_token(
            identity=str(user_data['user_id']),
            additional_claims={"roles": user_data['roles']}
        )
        return jsonify({
            "message": "Login exitoso",
            "access_token": access_token,
            "user": user_data
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── LOGOUT ────────────────────────────────────────────────────────────────────
@security_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        jwt_data = get_jwt()
        jti = jwt_data['jti']
        user_id = int(get_jwt_identity())
        # Calcular cuándo expira el token para registrarlo en blacklist
        exp_timestamp = jwt_data['exp']
        expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        result = SecurityService.logout_user(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── USUARIOS ──────────────────────────────────────────────────────────────────
@security_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    try:
        return jsonify({"data": SecurityService.get_all_users()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        return jsonify(SecurityService.soft_delete_user(user_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/users/<int:user_id>/roles', methods=['GET'])
@jwt_required()
def get_user_roles(user_id):
    try:
        return jsonify({"data": SecurityService.get_user_roles(user_id)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@security_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@jwt_required()
def assign_role_to_user(user_id):
    data = request.get_json()
    if not data or 'role_id' not in data:
        return jsonify({"error": "Se requiere 'role_id'"}), 400
    try:
        return jsonify(SecurityService.assign_role_to_user(
            user_id, data['role_id'])), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@security_bp.route('/users/<int:user_id>/roles/<int:role_id>',
                   methods=['DELETE'])
@jwt_required()
def revoke_role_from_user(user_id, role_id):
    try:
        return jsonify(SecurityService.revoke_role_from_user(
            user_id, role_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── ROLES ─────────────────────────────────────────────────────────────────────
@security_bp.route('/roles', methods=['POST'])
@jwt_required()
def create_role():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Se requiere 'name'"}), 400
    try:
        return jsonify({"message": "Rol creado",
                        "data": SecurityService.create_role(
                            name=data['name'],
                            description=data.get('description'))}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@security_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    try:
        return jsonify({"data": SecurityService.get_all_roles()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@jwt_required()
def delete_role(role_id):
    try:
        return jsonify(SecurityService.soft_delete_role(role_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@security_bp.route('/roles/<int:role_id>/permissions', methods=['GET'])
@jwt_required()
def get_role_permissions(role_id):
    try:
        return jsonify({"data": SecurityService.get_role_permissions(
            role_id)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@security_bp.route('/roles/<int:role_id>/permissions', methods=['POST'])
@jwt_required()
def assign_permission_to_role(role_id):
    data = request.get_json()
    if not data or 'permission_id' not in data:
        return jsonify({"error": "Se requiere 'permission_id'"}), 400
    try:
        return jsonify(SecurityService.assign_permission_to_role(
            role_id, data['permission_id'])), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@security_bp.route('/roles/<int:role_id>/permissions/<int:permission_id>',
                   methods=['DELETE'])
@jwt_required()
def revoke_permission_from_role(role_id, permission_id):
    try:
        return jsonify(SecurityService.revoke_permission_from_role(
            role_id, permission_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ── PERMISOS ──────────────────────────────────────────────────────────────────
@security_bp.route('/permissions', methods=['POST'])
@jwt_required()
def create_permission():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Se requiere 'name'"}), 400
    try:
        return jsonify({"message": "Permiso creado",
                        "data": SecurityService.create_permission(
                            name=data['name'],
                            description=data.get('description'))}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@security_bp.route('/permissions', methods=['GET'])
@jwt_required()
def get_permissions():
    try:
        return jsonify({"data": SecurityService.get_all_permissions()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/permissions/<int:permission_id>', methods=['DELETE'])
@jwt_required()
def delete_permission(permission_id):
    try:
        return jsonify(SecurityService.soft_delete_permission(
            permission_id)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    
    
@security_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user_profile(user_id):
    data = request.get_json()
    try:
        result = SecurityService.update_user_profile(user_id, data)
        return jsonify({"status": "success", "data": result}), 200
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": "Error interno del servidor"}), 500