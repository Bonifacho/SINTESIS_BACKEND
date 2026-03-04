from flask import Flask
from config import Config
from app.extensions import db, migrate, jwt
# Importar modelos para que Alembic los detecte
from app.core_security import models as security_models


def create_app(config_class=Config):
    """Fábrica de la aplicación Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar las extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    
    # Registrar Blueprints
    from app.core_security.routes import security_bp
    app.register_blueprint(security_bp)

    from app.core_academic.routes import academic_bp
    app.register_blueprint(academic_bp)
    
    # Importar modelos para que Alembic los detecte
    from app.core_security import models as security_models

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
    
    from app.core_security import models as security_models
    from app.core_academic import models as academic_models
    
    return app