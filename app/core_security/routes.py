from flask import Blueprint, request, jsonify
from app.core_security.services import SecurityService

# Creamos el Blueprint para el dominio de seguridad
security_bp = Blueprint('security', __name__, url_prefix='/api/v1/security')

@security_bp.route('/register', methods=['POST'])
def register():
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