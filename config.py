# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

FLASK_ENV = os.getenv('FLASK_ENV', 'development')
IS_PRODUCTION = (
    FLASK_ENV == 'production' or
    os.getenv('ENVIRONMENT') == 'production' or
    os.getenv('RENDER') is not None or
    os.getenv('RAILWAY_ENVIRONMENT') is not None
)

def _get_secret_key(var_name: str, dev_fallback: str) -> str:
    """Obtiene una clave secreta del entorno asegurando que en producción no use valores por defecto inseguros."""
    value = os.getenv(var_name)
    if IS_PRODUCTION:
        if not value or value in ('default_secret_key', 'super-llave-secreta-sintesis-2026', dev_fallback):
            raise ValueError(
                f"[SEGURIDAD CRÍTICA] La variable de entorno '{var_name}' debe estar definida con un valor seguro y único en producción."
            )
        return value
    return value or dev_fallback


class Config:
    """Configuración base — producción/desarrollo."""
    SECRET_KEY                   = _get_secret_key('SECRET_KEY', 'dev_secret_key_sintesis_local')
    # ¡AQUÍ ESTÁ EL CAMBIO CLAVE! Volvemos a DATABASE_URL
    SQLALCHEMY_DATABASE_URI      = os.getenv('DATABASE_URL') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ── Evita el error 500 (Lost connection to MySQL server / TiDB) ──
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
    
    JWT_SECRET_KEY               = _get_secret_key('JWT_SECRET_KEY', 'dev_jwt_secret_key_sintesis_local')
    JWT_ACCESS_TOKEN_EXPIRES     = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES    = timedelta(days=7)

class TestConfig(Config):
    """Configuración de pruebas — DB aislada, tokens cortos."""
    TESTING                  = True
    SQLALCHEMY_DATABASE_URI  = os.getenv('DATABASE_TEST_URL')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)