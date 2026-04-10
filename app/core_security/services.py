# app/core_security/services.py
from datetime import datetime, timezone
from app.extensions import db
from app.core_security.models import (
    Person, User, Role, Permission,
    UserHasRole, RoleHasPermission, BlacklistedToken
)
from app.core_security.repositories import SecurityRepository
from werkzeug.security import generate_password_hash, check_password_hash


class SecurityService:

    # ── REGISTRO ──────────────────────────────────────────────────────────────
    @staticmethod
    def register_user(first_name: str, last_name: str, document_id: str,
                      username: str, password: str, role_name: str) -> dict:
        """Crea una Persona, un Usuario y le asigna un rol en una sola operación."""

        if SecurityRepository.get_person_by_document(document_id):
            raise ValueError("Ya existe una persona con ese documento")

        if SecurityRepository.get_user_by_username(username):
            raise ValueError("El nombre de usuario ya está en uso")

        role = SecurityRepository.get_role_by_name(role_name)
        if not role or not role.is_active:
            raise ValueError(f"El rol '{role_name}' no existe o está inactivo")

        # Crear persona
        person = Person(
            first_name=first_name,
            last_name=last_name,
            document_id=document_id
        )
        SecurityRepository.create_person(person)

        # Crear usuario vinculado a la persona
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            person_id=person.id
        )
        SecurityRepository.create_user(user)

        # Asignar rol
        user_role = UserHasRole(user_id=user.id, role_id=role.id)
        SecurityRepository.assign_role_to_user(user_role)

        return {
            "id": user.id,
            "username": user.username,
            "full_name": f"{person.first_name} {person.last_name}",
            "role": role_name
        }

    # ── LOGIN ─────────────────────────────────────────────────────────────────
    @staticmethod
    def login_user(username: str, password: str) -> dict:
        """Valida credenciales y retorna datos del usuario para generar el JWT."""
        user = SecurityRepository.get_user_by_username(username)

        if not user or not user.is_active:
            raise ValueError("Usuario no encontrado o inactivo")

        if not check_password_hash(user.password_hash, password):
            raise ValueError("Contraseña incorrecta")

        # Obtener roles activos del usuario
        user_roles = SecurityRepository.get_roles_by_user(user.id)
        role_names = []
        for ur in user_roles:
            role = SecurityRepository.get_role_by_id(ur.role_id)
            if role and role.is_active:
                role_names.append(role.name)

        return {
            "user_id": user.id,
            "username": user.username,
            "roles": role_names
        }

    # ── LOGOUT ────────────────────────────────────────────────────────────────
    @staticmethod
    def logout_user(jti: str, user_id: int, expires_at: datetime) -> dict:
        """Revoca el JWT actual agregándolo a la blacklist."""
        token = BlacklistedToken(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at
        )
        SecurityRepository.add_token_to_blacklist(token)
        return {"message": "Sesión cerrada correctamente"}

    # ── ROLES ─────────────────────────────────────────────────────────────────
    @staticmethod
    def create_role(name: str, description: str = None) -> dict:
        if SecurityRepository.get_role_by_name(name):
            raise ValueError(f"El rol '{name}' ya existe")
        role = Role(name=name, description=description)
        created = SecurityRepository.create_role(role)
        return {
            "id": created.id,
            "name": created.name,
            "description": created.description,
            "is_active": created.is_active
        }

    @staticmethod
    def get_all_roles() -> list:
        roles = SecurityRepository.get_all_roles()
        return [{"id": r.id, "name": r.name,
                 "description": r.description} for r in roles]

    @staticmethod
    def soft_delete_role(role_id: int) -> dict:
        role = SecurityRepository.get_role_by_id(role_id)
        if not role or not role.is_active:
            raise ValueError("Rol no encontrado o ya inactivo")
        role.is_active = False
        db.session.commit()
        return {"message": f"Rol {role_id} desactivado (Soft Delete)"}

    # ── PERMISOS ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_permission(name: str, description: str = None) -> dict:
        if SecurityRepository.get_permission_by_name(name):
            raise ValueError(f"El permiso '{name}' ya existe")
        permission = Permission(name=name, description=description)
        created = SecurityRepository.create_permission(permission)
        return {
            "id": created.id,
            "name": created.name,
            "description": created.description,
            "is_active": created.is_active
        }

    @staticmethod
    def get_all_permissions() -> list:
        permissions = SecurityRepository.get_all_permissions()
        return [{"id": p.id, "name": p.name,
                 "description": p.description} for p in permissions]

    @staticmethod
    def soft_delete_permission(permission_id: int) -> dict:
        p = SecurityRepository.get_permission_by_id(permission_id)
        if not p or not p.is_active:
            raise ValueError("Permiso no encontrado o ya inactivo")
        p.is_active = False
        db.session.commit()
        return {"message": f"Permiso {permission_id} desactivado (Soft Delete)"}

    # ── ASIGNACIÓN ROL → USUARIO ──────────────────────────────────────────────
    @staticmethod
    def assign_role_to_user(user_id: int, role_id: int) -> dict:
        user = SecurityRepository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("Usuario no encontrado o inactivo")

        role = SecurityRepository.get_role_by_id(role_id)
        if not role or not role.is_active:
            raise ValueError("Rol no encontrado o inactivo")

        if SecurityRepository.get_user_role(user_id, role_id):
            raise ValueError("El usuario ya tiene ese rol asignado")

        user_role = UserHasRole(user_id=user_id, role_id=role_id)
        SecurityRepository.assign_role_to_user(user_role)
        return {
            "message": f"Rol '{role.name}' asignado al usuario '{user.username}'",
            "user_id": user_id,
            "role_id": role_id
        }

    @staticmethod
    def revoke_role_from_user(user_id: int, role_id: int) -> dict:
        user_role = SecurityRepository.get_user_role(user_id, role_id)
        if not user_role:
            raise ValueError("El usuario no tiene ese rol asignado")
        user_role.is_active = False
        db.session.commit()
        return {"message": "Rol revocado correctamente"}

    @staticmethod
    def get_user_roles(user_id: int) -> list:
        user = SecurityRepository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("Usuario no encontrado o inactivo")
        user_roles = SecurityRepository.get_roles_by_user(user_id)
        result = []
        for ur in user_roles:
            role = SecurityRepository.get_role_by_id(ur.role_id)
            if role:
                result.append({"id": role.id, "name": role.name,
                               "description": role.description})
        return result

    # ── ASIGNACIÓN PERMISO → ROL ──────────────────────────────────────────────
    @staticmethod
    def assign_permission_to_role(role_id: int, permission_id: int) -> dict:
        role = SecurityRepository.get_role_by_id(role_id)
        if not role or not role.is_active:
            raise ValueError("Rol no encontrado o inactivo")

        permission = SecurityRepository.get_permission_by_id(permission_id)
        if not permission or not permission.is_active:
            raise ValueError("Permiso no encontrado o inactivo")

        if SecurityRepository.get_role_permission(role_id, permission_id):
            raise ValueError("El rol ya tiene ese permiso asignado")

        rhp = RoleHasPermission(role_id=role_id, permission_id=permission_id)
        SecurityRepository.assign_permission_to_role(rhp)
        return {
            "message": f"Permiso '{permission.name}' asignado al rol '{role.name}'",
            "role_id": role_id,
            "permission_id": permission_id
        }

    @staticmethod
    def revoke_permission_from_role(role_id: int, permission_id: int) -> dict:
        rhp = SecurityRepository.get_role_permission(role_id, permission_id)
        if not rhp:
            raise ValueError("El rol no tiene ese permiso asignado")
        rhp.is_active = False
        db.session.commit()
        return {"message": "Permiso revocado correctamente"}

    @staticmethod
    def get_role_permissions(role_id: int) -> list:
        role = SecurityRepository.get_role_by_id(role_id)
        if not role or not role.is_active:
            raise ValueError("Rol no encontrado o inactivo")
        role_permissions = SecurityRepository.get_permissions_by_role(role_id)
        result = []
        for rp in role_permissions:
            p = SecurityRepository.get_permission_by_id(rp.permission_id)
            if p:
                result.append({"id": p.id, "name": p.name,
                               "description": p.description})
        return result

    # ── CONSULTAS DE USUARIOS ─────────────────────────────────────────────────
    @staticmethod
    def get_all_users() -> list:
        users = SecurityRepository.get_all_users()
        result = []
        for u in users:
            person = SecurityRepository.get_person_by_id(u.person_id)
            user_roles = SecurityRepository.get_roles_by_user(u.id)
            roles = []
            for ur in user_roles:
                role = SecurityRepository.get_role_by_id(ur.role_id)
                if role:
                    roles.append(role.name)
            result.append({
                "id": u.id,
                "username": u.username,
                "full_name": f"{person.first_name} {person.last_name}" if person else "",
                "document_id": person.document_id if person else "",
                "roles": roles,
                "is_active": u.is_active
            })
        return result

    @staticmethod
    def soft_delete_user(user_id: int) -> dict:
        user = SecurityRepository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("Usuario no encontrado o ya inactivo")
        user.is_active = False
        db.session.commit()
        return {"message": f"Usuario {user_id} desactivado (Soft Delete)"}
    
    @staticmethod
    def update_user_profile(user_id: int, data: dict) -> dict:
        user = SecurityRepository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("Usuario no encontrado o inactivo")
        
        person = SecurityRepository.get_person_by_id(user.person_id)
        if person:
            if 'first_name' in data: person.first_name = data['first_name']
            if 'last_name' in data: person.last_name = data['last_name']
            if 'document_id' in data: person.document_id = data['document_id']
            
        from app.extensions import db
        db.session.commit()
        return {"message": "Perfil actualizado exitosamente"}