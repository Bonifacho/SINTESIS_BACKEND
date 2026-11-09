# app/utils/decorators.py
import time
import threading
from collections import defaultdict, deque
from functools import wraps
from flask import jsonify, request, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from app.extensions import db

_RATE_LIMIT_BUCKETS: dict[str, deque] = defaultdict(deque)
_RATE_LIMIT_LOCK = threading.Lock()


def clear_rate_limit_buckets():
    """Limpia los contadores del rate limiter en memoria (útil en pruebas)."""
    with _RATE_LIMIT_LOCK:
        _RATE_LIMIT_BUCKETS.clear()


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """Decorador ligero de Rate Limiting por ventana deslizante (IP + endpoint).
    Protege endpoints críticos de autenticación contra ataques de fuerza bruta (OWASP API4:2023).
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if current_app.config.get("TESTING") and not current_app.config.get("ENABLE_RATE_LIMIT_IN_TESTS"):
                return fn(*args, **kwargs)

            client_ip = (
                request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                or request.remote_addr
                or "unknown"
            )
            bucket_key = f"{request.endpoint}:{client_ip}"
            now = time.monotonic()

            with _RATE_LIMIT_LOCK:
                dq = _RATE_LIMIT_BUCKETS[bucket_key]
                while dq and (now - dq[0]) > window_seconds:
                    dq.popleft()
                if len(dq) >= max_requests:
                    return jsonify({
                        "error": "Demasiadas peticiones. Por favor intente nuevamente más tarde.",
                        "code": 429
                    }), 429
                dq.append(now)

            return fn(*args, **kwargs)
        return decorator
    return wrapper


def safe_internal_error(exc: Exception, use_status_envelope: bool = False):
    """Realiza rollback preventivo de la sesión SQLAlchemy, registra el error internamente
    y retorna un mensaje HTTP 500 sanitizado sin exponer trazas ni detalles de BD (OWASP API8:2023).
    """
    try:
        db.session.rollback()
    except Exception:
        pass
    current_app.logger.exception("Error interno no controlado en endpoint: %s", exc)
    if use_status_envelope:
        return jsonify({"status": "error", "message": "Error interno del servidor"}), 500
    return jsonify({"error": "Error interno del servidor"}), 500


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
