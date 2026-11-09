# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

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


def _build_engine_options(db_uri: str | None) -> dict:
    """Construye las opciones del Connection Pool de SQLAlchemy para MySQL / TiDB Cloud.
    Para motores en memoria como SQLite (pruebas aisladas), omite parámetros exclusivos de QueuePool.
    """
    if db_uri and db_uri.startswith("sqlite"):
        return {"pool_pre_ping": True}

    return {
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", 280)),
        "pool_size": int(os.getenv("DB_POOL_SIZE", 10)),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 20)),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", 15)),
        "pool_use_lifo": True,
        "connect_args": {
            "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", 10)),
        },
    }


class Config:
    """Configuración base — producción/desarrollo."""
    _build_engine_options = staticmethod(_build_engine_options)
    SECRET_KEY = _get_secret_key('SECRET_KEY', 'dev_secret_key_sintesis_local')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Connection Pooling optimizado para TiDB Cloud Serverless y MySQL ──
    SQLALCHEMY_ENGINE_OPTIONS = _build_engine_options(SQLALCHEMY_DATABASE_URI)

    JWT_SECRET_KEY = _get_secret_key('JWT_SECRET_KEY', 'dev_jwt_secret_key_sintesis_local')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)


class TestConfig(Config):
    """Configuración de pruebas — DB aislada, tokens cortos."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_TEST_URL') or os.getenv('DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = _build_engine_options(SQLALCHEMY_DATABASE_URI)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
