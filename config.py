# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración base — producción/desarrollo."""
    SECRET_KEY                   = os.getenv('SECRET_KEY', 'default_secret_key')
    # ¡AQUÍ ESTÁ EL CAMBIO CLAVE! Volvemos a DATABASE_URL
    SQLALCHEMY_DATABASE_URI      = os.getenv('DATABASE_URL') 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY               = os.getenv('JWT_SECRET_KEY', 'super-llave-secreta-sintesis-2026')
    JWT_ACCESS_TOKEN_EXPIRES     = timedelta(hours=8)

class TestConfig(Config):
    """Configuración de pruebas — DB aislada, tokens cortos."""
    TESTING                  = True
    SQLALCHEMY_DATABASE_URI  = os.getenv('DATABASE_TEST_URL')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)