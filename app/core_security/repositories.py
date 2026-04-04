# app/core_security/repositories.py
from app.extensions import db
from app.core_security.models import (
    Person, User, Role, Permission,
    UserHasRole, RoleHasPermission, BlacklistedToken
)


class SecurityRepository:

    # ── PERSONAS ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_person(person: Person) -> Person:
        db.session.add(person)
        db.session.flush()
        return person

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
    def create_user(user: User) -> User:
        db.session.add(user)
        db.session.commit()
        return user

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
    def create_role(role: Role) -> Role:
        db.session.add(role)
        db.session.commit()
        return role

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
    def create_permission(permission: Permission) -> Permission:
        db.session.add(permission)
        db.session.commit()
        return permission

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
    def assign_role_to_user(user_has_role: UserHasRole) -> UserHasRole:
        db.session.add(user_has_role)
        db.session.commit()
        return user_has_role

    @staticmethod
    def get_user_role(user_id: int, role_id: int) -> UserHasRole:
        return db.session.query(UserHasRole).filter_by(
            user_id=user_id, role_id=role_id, is_active=True).first()

    @staticmethod
    def get_roles_by_user(user_id: int):
        return db.session.query(UserHasRole).filter_by(
            user_id=user_id, is_active=True).all()

    # ── ROLE HAS PERMISSION ───────────────────────────────────────────────────
    @staticmethod
    def assign_permission_to_role(rhp: RoleHasPermission) -> RoleHasPermission:
        db.session.add(rhp)
        db.session.commit()
        return rhp

    @staticmethod
    def get_role_permission(role_id: int, permission_id: int) -> RoleHasPermission:
        return db.session.query(RoleHasPermission).filter_by(
            role_id=role_id, permission_id=permission_id,
            is_active=True).first()

    @staticmethod
    def get_permissions_by_role(role_id: int):
        return db.session.query(RoleHasPermission).filter_by(
            role_id=role_id, is_active=True).all()

    # ── BLACKLISTED TOKENS ────────────────────────────────────────────────────
    @staticmethod
    def add_token_to_blacklist(token: BlacklistedToken) -> BlacklistedToken:
        db.session.add(token)
        db.session.commit()
        return token

    @staticmethod
    def is_token_blacklisted(jti: str) -> bool:
        """Verifica si un JTI ya fue revocado. Se llama en cada request."""
        return db.session.query(BlacklistedToken).filter_by(
            jti=jti).first() is not None