# app/core_security/models.py
from app.extensions import db
from datetime import datetime, timezone


# ─────────────────────────────────────────────────────────────────────────────
# PERSONAS — datos personales desacoplados de la cuenta
# ─────────────────────────────────────────────────────────────────────────────
class Person(db.Model):
    __tablename__ = 'persons'

    id          = db.Column(db.Integer, primary_key=True)
    first_name  = db.Column(db.String(100), nullable=False)
    last_name   = db.Column(db.String(100), nullable=False)
    document_id = db.Column(db.String(50), unique=True, nullable=False)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active   = db.Column(db.Boolean, default=True, nullable=False)

    user = db.relationship('User', backref='person', uselist=False,
                           cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────────────
# USUARIOS — credenciales de acceso
# role_id eliminado: la asignación de roles va por UserHasRole
# ─────────────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    person_id     = db.Column(db.Integer, db.ForeignKey('persons.id'),
                              nullable=False, unique=True)
    is_active     = db.Column(db.Boolean, default=True, nullable=False)

    # Relaciones
    roles  = db.relationship('UserHasRole', backref='user',
                             lazy='dynamic', cascade="all, delete-orphan")
    tokens = db.relationship('BlacklistedToken', backref='user',
                             lazy='dynamic', cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────────────
# ROLES — perfiles de acceso del sistema
# Valores esperados: 'docente', 'estudiante', 'practicante'
# ─────────────────────────────────────────────────────────────────────────────
class Role(db.Model):
    __tablename__ = 'roles'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)

    # Relaciones
    users       = db.relationship('UserHasRole', backref='role',
                                  lazy='dynamic', cascade="all, delete-orphan")
    permissions = db.relationship('RoleHasPermission', backref='role',
                                  lazy='dynamic', cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────────────
# PERMISOS — acciones granulares del sistema
# Ejemplos: 'group:read', 'group:write', 'exam:grade', 'ova:read'
# ─────────────────────────────────────────────────────────────────────────────
class Permission(db.Model):
    __tablename__ = 'permissions'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)

    roles = db.relationship('RoleHasPermission', backref='permission',
                            lazy='dynamic', cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────────────
# TABLA PIVOTE — Usuario ↔ Rol (muchos a muchos)
# Un usuario puede tener múltiples roles
# ─────────────────────────────────────────────────────────────────────────────
class UserHasRole(db.Model):
    __tablename__ = 'user_has_role'

    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_id   = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    )


# ─────────────────────────────────────────────────────────────────────────────
# TABLA PIVOTE — Rol ↔ Permiso (muchos a muchos)
# Un rol puede tener múltiples permisos
# ─────────────────────────────────────────────────────────────────────────────
class RoleHasPermission(db.Model):
    __tablename__ = 'role_has_permission'

    id            = db.Column(db.Integer, primary_key=True)
    role_id       = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'),
                              nullable=False)
    is_active     = db.Column(db.Boolean, default=True, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )


# ─────────────────────────────────────────────────────────────────────────────
# TOKENS EN LISTA NEGRA — logout seguro (Tríada CIA — Confidencialidad)
# Cada JWT revocado se registra aquí hasta su fecha de expiración
# ─────────────────────────────────────────────────────────────────────────────
class BlacklistedToken(db.Model):
    __tablename__ = 'blacklisted_tokens'

    id              = db.Column(db.Integer, primary_key=True)
    jti             = db.Column(db.String(36), unique=True, nullable=False)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'),
                                nullable=False)
    blacklisted_at  = db.Column(db.DateTime,
                                default=lambda: datetime.now(timezone.utc))
    expires_at      = db.Column(db.DateTime, nullable=False)
    
    
# ─────────────────────────────────────────────────────────────────────────────
# CAPA 5 — Acceso de practicantes a grupos (nuevo)
# ─────────────────────────────────────────────────────────────────────────────

