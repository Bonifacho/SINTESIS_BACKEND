from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Este es el bloque que debemos añadir para la seguridad V2
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    from app.core_security.models import BlacklistedToken
    jti = jwt_payload["jti"]
    token = db.session.query(BlacklistedToken.id).filter_by(jti=jti).scalar()
    return token is not None