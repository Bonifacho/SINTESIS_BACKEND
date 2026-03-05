from flask import Blueprint, request, jsonify
from app.core_security.services import SecurityService
from flask_jwt_extended import jwt_required

# Creamos el Blueprint para el dominio de seguridad
security_bp = Blueprint('security', __name__, url_prefix='/api/v1/security')

# ==========================================
# AUTENTICACIÓN (LOGIN / REGISTER)
# ==========================================

@security_bp.route('/register', methods=['POST'])
def register():
    """Ruta para registrar un nuevo usuario con su persona y rol asociado."""
    data = request.get_json()
    
    # Validación básica MVP
    if not data or 'person' not in data or 'user' not in data or 'role' not in data:
        return jsonify({"error": "Estructura JSON inválida. Faltan datos (person, user, role)"}), 400
        
    try:
        # Delegamos la lógica al Service
        new_user = SecurityService.register_user(
            person_data=data['person'],
            user_data=data['user'],
            role_name=data['role']
        )
        return jsonify({
            "message": "Usuario registrado con éxito", 
            "data": new_user
        }), 201
        
    except Exception as e:
        # Captura de errores (ej. usuario o documento duplicado)
        return jsonify({"error": str(e)}), 500
    
@security_bp.route('/login', methods=['POST'])
def login():
    """Ruta para autenticarse y obtener un token JWT."""
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Faltan credenciales (username y password)"}), 400
        
    try:
        result = SecurityService.login(
            username=data['username'],
            password=data['password']
        )
        return jsonify(result), 200
        
    except ValueError as e:
        # Error 401 Unauthorized si la clave está mal
        return jsonify({"error": str(e)}), 401 
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# RUTAS CRUD DE ROLES
# ==========================================

@security_bp.route('/roles', methods=['POST'])
@jwt_required()
def create_role():
    """Ruta para crear un nuevo rol en el sistema."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Falta el campo 'name'"}), 400
    try:
        new_role = SecurityService.create_role(
            name=data['name'],
            description=data.get('description')
        )
        return jsonify({"message": "Rol creado con éxito", "data": new_role}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_all_roles():
    """Ruta para consultar todos los roles activos."""
    try:
        roles = SecurityService.get_all_roles()
        return jsonify({"message": "Roles recuperados con éxito", "data": roles}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/roles/<int:role_id>', methods=['GET'])
@jwt_required()
def get_role(role_id):
    """Ruta para consultar un rol específico por su ID."""
    try:
        role = SecurityService.get_role_by_id(role_id)
        return jsonify({"message": "Rol recuperado con éxito", "data": role}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/roles/<int:role_id>', methods=['PUT'])
@jwt_required()
def update_role(role_id):
    """Ruta para actualizar los datos de un rol existente."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Faltan datos a actualizar"}), 400
    try:
        updated = SecurityService.update_role(
            role_id,
            name=data.get('name'),
            description=data.get('description')
        )
        return jsonify({"message": "Rol actualizado con éxito", "data": updated}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@jwt_required()
def delete_role(role_id):
    """Ruta para desactivar un rol (Soft Delete)."""
    try:
        result = SecurityService.soft_delete_role(role_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# RUTAS CRUD DE PERSONAS
# ==========================================

@security_bp.route('/persons', methods=['GET'])
@jwt_required()
def get_all_persons():
    """Ruta para consultar todas las personas activas registradas."""
    try:
        persons = SecurityService.get_all_persons()
        return jsonify({"message": "Personas recuperadas con éxito", "data": persons}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/persons/<int:person_id>', methods=['GET'])
@jwt_required()
def get_person(person_id):
    """Ruta para consultar una persona específica por su ID."""
    try:
        person = SecurityService.get_person_by_id(person_id)
        return jsonify({"message": "Persona recuperada con éxito", "data": person}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/persons/<int:person_id>', methods=['PUT'])
@jwt_required()
def update_person(person_id):
    """Ruta para actualizar los datos de una persona (nombre, apellido, documento)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Faltan datos a actualizar"}), 400
    try:
        updated = SecurityService.update_person(person_id, data)
        return jsonify({"message": "Persona actualizada con éxito", "data": updated}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/persons/<int:person_id>', methods=['DELETE'])
@jwt_required()
def delete_person(person_id):
    """Ruta para desactivar una persona (Soft Delete)."""
    try:
        result = SecurityService.soft_delete_person(person_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# RUTAS CRUD DE USUARIOS
# ==========================================

@security_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Ruta para consultar todos los usuarios activos del sistema."""
    try:
        users = SecurityService.get_all_users()
        return jsonify({"message": "Usuarios recuperados con éxito", "data": users}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Ruta para consultar un usuario específico por su ID."""
    try:
        user = SecurityService.get_user_by_id(user_id)
        return jsonify({"message": "Usuario recuperado con éxito", "data": user}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Ruta para actualizar un usuario (contraseña y/o rol)."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Faltan datos a actualizar (password y/o role)"}), 400
    try:
        updated = SecurityService.update_user(user_id, data)
        return jsonify({"message": "Usuario actualizado con éxito", "data": updated}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@security_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Ruta para desactivar un usuario (Soft Delete)."""
    try:
        result = SecurityService.soft_delete_user(user_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500