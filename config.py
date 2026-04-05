import os   
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    """Configuración base de la aplicación."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'super-llave-secreta-sintesis-2026')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)