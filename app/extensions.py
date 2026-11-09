from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Verificación SARGable y parametrizada de revocación de JWT en cada request
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    from app.core_security.repositories import SecurityRepository
    jti = jwt_payload.get("jti")
    if not jti:
        return True
    return SecurityRepository.is_token_blacklisted(jti)
