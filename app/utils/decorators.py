# app/utils/decorators.py
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from functools import wraps
from flask import jsonify


def role_required(*role_names):
    """Decorador RBAC: restringe el acceso a usuarios con al menos uno de los roles indicados.

    Uso:
        @role_required('docente')              # un solo rol
        @role_required('docente', 'administrador')  # cualquiera de los dos
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_roles = claims.get("roles", [])

            if not any(r in user_roles for r in role_names):
                return jsonify({
                    "error": f"Acceso denegado. Se requiere uno de los siguientes roles: {list(role_names)}"
                }), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper
