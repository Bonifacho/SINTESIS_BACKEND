# app/core_security/repositories.py
from app.extensions import db
from app.utils.database import persist_entity
from app.core_security.models import (
    Person, User, Role, Permission,
    UserHasRole, RoleHasPermission, BlacklistedToken,
    PasswordResetToken
)


class SecurityRepository:

    # ── PERSONAS ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_person(person: Person, commit: bool = False) -> Person:
        return persist_entity(person, commit=commit)

    @staticmethod
    def get_person_by_id(person_id: int) -> Person:
        return db.session.query(Person).filter_by(id=person_id).first()

    @staticmethod
    def get_person_by_document(document_id: str) -> Person:
        return db.session.query(Person).filter_by(
            document_id=document_id).first()

    @staticmethod
    def get_all_persons():
        return db.session.query(Person).filter_by(is_active=True).all()

    # ── USUARIOS ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_user(user: User, commit: bool = True) -> User:
        return persist_entity(user, commit=commit)

    @staticmethod
    def get_user_by_id(user_id: int) -> User:
        return db.session.query(User).filter_by(id=user_id).first()

    @staticmethod
    def get_user_by_username(username: str) -> User:
        return db.session.query(User).filter_by(username=username).first()

    @staticmethod
    def get_all_users():
        return db.session.query(User).filter_by(is_active=True).all()

    # ── ROLES ─────────────────────────────────────────────────────────────────
    @staticmethod
    def create_role(role: Role, commit: bool = True) -> Role:
        return persist_entity(role, commit=commit)

    @staticmethod
    def get_role_by_id(role_id: int) -> Role:
        return db.session.query(Role).filter_by(id=role_id).first()

    @staticmethod
    def get_role_by_name(name: str) -> Role:
        return db.session.query(Role).filter_by(name=name).first()

    @staticmethod
    def get_all_roles():
        return db.session.query(Role).filter_by(is_active=True).all()

    # ── PERMISOS ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_permission(permission: Permission, commit: bool = True) -> Permission:
        return persist_entity(permission, commit=commit)

    @staticmethod
    def get_permission_by_id(permission_id: int) -> Permission:
        return db.session.query(Permission).filter_by(
            id=permission_id).first()

    @staticmethod
    def get_permission_by_name(name: str) -> Permission:
        return db.session.query(Permission).filter_by(name=name).first()

    @staticmethod
    def get_all_permissions():
        return db.session.query(Permission).filter_by(is_active=True).all()

    # ── USER HAS ROLE ─────────────────────────────────────────────────────────
    @staticmethod
    def assign_role_to_user(user_has_role: UserHasRole, commit: bool = True) -> UserHasRole:
        return persist_entity(user_has_role, commit=commit)

    @staticmethod
    def get_user_role(user_id: int, role_id: int) -> UserHasRole:
        return db.session.query(UserHasRole).filter_by(
            user_id=user_id, role_id=role_id, is_active=True).first()

    @staticmethod
    def get_user_role_any(user_id: int, role_id: int) -> UserHasRole:
        """Busca asignación de rol incluyendo registros inactivos (soft-delete)."""
        return db.session.query(UserHasRole).filter_by(
            user_id=user_id, role_id=role_id).first()

    @staticmethod
    def get_roles_by_user(user_id: int):
        return db.session.query(UserHasRole).filter_by(
            user_id=user_id, is_active=True).all()

    # ── ROLE HAS PERMISSION ───────────────────────────────────────────────────
    @staticmethod
    def assign_permission_to_role(rhp: RoleHasPermission, commit: bool = True) -> RoleHasPermission:
        return persist_entity(rhp, commit=commit)

    @staticmethod
    def get_role_permission(role_id: int, permission_id: int) -> RoleHasPermission:
        return db.session.query(RoleHasPermission).filter_by(
            role_id=role_id, permission_id=permission_id,
            is_active=True).first()

    @staticmethod
    def get_role_permission_any(role_id: int, permission_id: int) -> RoleHasPermission:
        """Busca permiso de rol incluyendo registros inactivos (soft-delete)."""
        return db.session.query(RoleHasPermission).filter_by(
            role_id=role_id, permission_id=permission_id).first()

    @staticmethod
    def get_permissions_by_role(role_id: int):
        return db.session.query(RoleHasPermission).filter_by(
            role_id=role_id, is_active=True).all()

    # ── BLACKLISTED TOKENS ────────────────────────────────────────────────────
    @staticmethod
    def add_token_to_blacklist(token: BlacklistedToken, commit: bool = True) -> BlacklistedToken:
        return persist_entity(token, commit=commit)

    @staticmethod
    def is_token_blacklisted(jti: str) -> bool:
        """Verifica si un JTI ya fue revocado. Se llama en cada request."""
        return db.session.query(BlacklistedToken).filter_by(
            jti=jti).first() is not None

    # ── TOKENS DE RECUPERACIÓN DE CONTRASEÑA ──────────────────────────────────
    @staticmethod
    def create_password_reset_token(token: 'PasswordResetToken', commit: bool = True) -> 'PasswordResetToken':
        return persist_entity(token, commit=commit)

    @staticmethod
    def get_password_reset_token(token_hash: str) -> 'PasswordResetToken':
        return db.session.query(PasswordResetToken).filter_by(token_hash=token_hash).first()
