from flask import Flask, jsonify
from config import Config
from app.extensions import db, migrate, jwt
# Importar modelos para que Alembic los detecte
from app.core_security import models as security_models
from app.core_academic import models as academic_models


def create_app(config_class=Config):
    """Fábrica de la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar las extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # ── Error Handlers Globales ───────────────────────────────────────────
    # Garantizan que TODA respuesta de error sea JSON parseable
    # por el interceptor Axios del frontend móvil.

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Petición inválida", "code": 400}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "No autenticado — token ausente o inválido", "code": 401}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": "Acceso denegado — permisos insuficientes", "code": 403}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Recurso no encontrado", "code": 404}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Método HTTP no permitido", "code": 405}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Error interno del servidor", "code": 500}), 500

    # ── Callbacks de flask-jwt-extended ────────────────────────────────────
    # Sobreescriben las respuestas por defecto de la extensión para que
    # el frontend reciba JSON consistente en vez de mensajes genéricos.

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token expirado", "code": 401}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error_string):
        return jsonify({"error": f"Token inválido: {error_string}", "code": 401}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error_string):
        return jsonify({"error": "Token de autorización requerido", "code": 401}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token revocado (sesión cerrada)", "code": 401}), 401

    # ── Registrar Blueprints ──────────────────────────────────────────────
    from app.core_security.routes import security_bp
    app.register_blueprint(security_bp)

    from app.core_academic.routes import academic_bp
    app.register_blueprint(academic_bp)

    # ── Rutas de salud ────────────────────────────────────────────────────
    @app.route('/health')
    def health_check():
        return {"status": "ok", "message": "SÍNTESIS API corriendo correctamente."}

    @app.route('/')
    def index():
        return {
            "api": "SÍNTESIS (Sistema INtegral Tecnológico)",
            "version": "1.0 MVP",
            "status": "Online"
        }

    return app