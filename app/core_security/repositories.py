# app/core_security/repositories.py
from datetime import datetime, timezone
from sqlalchemy import text, bindparam, Integer, String, DateTime
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
    def get_user_by_identifier(identifier: str) -> User:
        """Busca usuario activo por username (índice único) o por email de persona (idx_person_email_active)."""
        ident = (identifier or "").strip()
        user = db.session.query(User).filter_by(username=ident, is_active=True).first()
        if user:
            return user
        return (
            db.session.query(User)
            .join(Person, User.person_id == Person.id)
            .filter(
                Person.email == ident,
                Person.is_active == True,
                User.is_active == True,
            )
            .first()
        )

    @staticmethod
    def get_all_users():
        return db.session.query(User).filter_by(is_active=True).all()

    @staticmethod
    def get_all_users_enriched() -> list[dict]:
        """Consulta SARGable y parametrizada que reemplaza el doble bucle N+1 (2N+1 queries -> 2 queries)."""
        users_stmt = text("""
            SELECT
                u.id AS id,
                u.username AS username,
                u.is_active AS is_active,
                p.first_name AS first_name,
                p.last_name AS last_name,
                p.document_id AS document_id
            FROM users u
            LEFT JOIN persons p ON p.id = u.person_id
            WHERE u.is_active = :active_flag
            ORDER BY u.id ASC
        """).bindparams(
            bindparam("active_flag", value=1, type_=Integer)
        )
        user_rows = db.session.execute(users_stmt).mappings().all()
        if not user_rows:
            return []

        roles_stmt = text("""
            SELECT
                uhr.user_id AS user_id,
                r.name AS role_name
            FROM user_has_role uhr
            INNER JOIN roles r ON r.id = uhr.role_id
            WHERE uhr.is_active = :active_flag
              AND r.is_active = :active_flag
        """).bindparams(
            bindparam("active_flag", value=1, type_=Integer)
        )
        role_rows = db.session.execute(roles_stmt).mappings().all()
        roles_by_user: dict[int, list[str]] = {}
        for rr in role_rows:
            roles_by_user.setdefault(rr["user_id"], []).append(rr["role_name"])

        result = []
        for u in user_rows:
            first_name = u["first_name"] or ""
            last_name = u["last_name"] or ""
            full_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else ""
            result.append({
                "id": u["id"],
                "username": u["username"],
                "full_name": full_name,
                "document_id": u["document_id"] or "",
                "roles": roles_by_user.get(u["id"], []),
                "is_active": bool(u["is_active"]),
            })
        return result

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

    @staticmethod
    def get_active_roles_for_user(user_id: int) -> list[Role]:
        """Retorna las entidades Role activas de un usuario en una sola consulta JOIN SARGable."""
        return (
            db.session.query(Role)
            .join(UserHasRole, UserHasRole.role_id == Role.id)
            .filter(
                UserHasRole.user_id == int(user_id),
                UserHasRole.is_active == True,
                Role.is_active == True,
            )
            .all()
        )

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
        """Verifica si un JTI fue revocado usando SQL explícitamente parametrizado y covering index."""
        stmt = text("""
            SELECT 1
            FROM blacklisted_tokens
            WHERE jti = :jti
            LIMIT 1
        """).bindparams(
            bindparam("jti", value=str(jti), type_=String(36))
        )
        return db.session.execute(stmt).scalar() is not None

    # ── TOKENS DE RECUPERACIÓN DE CONTRASEÑA ──────────────────────────────────
    @staticmethod
    def create_password_reset_token(token: 'PasswordResetToken', commit: bool = True) -> 'PasswordResetToken':
        return persist_entity(token, commit=commit)

    @staticmethod
    def get_password_reset_token(token_hash: str) -> 'PasswordResetToken':
        return db.session.query(PasswordResetToken).filter_by(token_hash=token_hash).first()

    @staticmethod
    def get_password_reset_token_for_update(token_hash: str) -> 'PasswordResetToken':
        """Obtiene el token de recuperación aplicando bloqueo pesimista SELECT ... FOR UPDATE."""
        return (
            db.session.query(PasswordResetToken)
            .filter_by(token_hash=str(token_hash))
            .with_for_update()
            .first()
        )

    @staticmethod
    def invalidate_active_reset_tokens(user_id: int) -> int:
        """Invalida en una sola sentencia SARGable todos los tokens previos no usados del usuario."""
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        stmt = text("""
            UPDATE password_reset_tokens
            SET is_used = 1
            WHERE user_id = :uid
              AND is_used = 0
              AND expires_at > :now_utc
        """).bindparams(
            bindparam("uid", value=int(user_id), type_=Integer),
            bindparam("now_utc", value=now_utc, type_=DateTime),
        )
        res = db.session.execute(stmt)
        return res.rowcount
