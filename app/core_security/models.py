from app.extensions import db
from datetime import datetime, timezone

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # ej: 'docente', 'estudiante'
    description = db.Column(db.String(255), nullable=True)
    
    # Relación bidireccional (Corregido a backref)
    users = db.relationship('User', backref='role', lazy='dynamic')

class Person(db.Model):
    __tablename__ = 'persons'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    document_id = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relación 1 a 1 con User (Corregido a backref)
    user = db.relationship('User', backref='person', uselist=False, cascade="all, delete-orphan")

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Claves foráneas
    person_id = db.Column(db.Integer, db.ForeignKey('persons.id'), nullable=False, unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)