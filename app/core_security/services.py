# app/core_security/services.py
from datetime import datetime, timezone
from app.extensions import db
from app.utils.database import transactional_session
from app.core_security.models import (
    Person, User, Role, Permission,
    UserHasRole, RoleHasPermission, BlacklistedToken
)
from app.core_security.repositories import SecurityRepository
from werkzeug.security import generate_password_hash, check_password_hash
import re

def validate_document_id(document_id: str) -> str:
    """Valida que el documento de identidad sea numérico y tenga longitud válida."""
    cleaned = document_id.strip()
    
    if not cleaned:
        raise ValueError("El documento de identidad es obligatorio.")
    
    if not re.match(r'^\d{5,15}$', cleaned):
        raise ValueError("El documento debe contener solo números (entre 5 y 15 dígitos).")
    
    return cleaned

class SecurityService:

    # ── REGISTRO ──────────────────────────────────────────────────────────────
    @staticmethod
    def register_user(first_name: str, last_name: str, document_id: str,
                      username: str, password: str, role_name: str = "estudiante", **kwargs) -> dict:
        """Crea una Persona, un Usuario y le asigna un rol (por defecto 'estudiante').
        """
        
        document_id = validate_document_id(document_id)

        # ── Validaciones de unicidad ──────────────────────────────────────
        if SecurityRepository.get_person_by_document(document_id):
            raise ValueError("Ya existe una persona con ese documento")

        if SecurityRepository.get_user_by_username(username):
            raise ValueError("El nombre de usuario ya está en uso")

        # ── Validar rol ───────────────────────────────────────────────────
        role = SecurityRepository.get_role_by_name(role_name)
        if not role or not role.is_active:
            raise ValueError(
                f"El rol '{role_name}' no existe o está inactivo en la base de datos."
            )

        # ── Transacción atómica ACID: Persona + Usuario + Rol (Todo o Nada) ──
        with transactional_session():
            # ── Crear persona ─────────────────────────────────────────────────
            person = Person(
                first_name=first_name,
                last_name=last_name,
                document_id=document_id
            )
            SecurityRepository.create_person(person, commit=False)

            # ── Crear usuario vinculado a la persona ─────────────────────────
            user = User(
                username=username,
                password_hash=generate_password_hash(password),
                person_id=person.id
            )
            SecurityRepository.create_user(user, commit=False)

            # ── Asignar rol ───────────────────────────────────────────────────
            user_role = UserHasRole(user_id=user.id, role_id=role.id)
            SecurityRepository.assign_role_to_user(user_role, commit=False)

        return {
            "id": user.id,
            "username": user.username,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "full_name": f"{person.first_name} {person.last_name}",
            "role": role.name
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

        # Obtener datos de la persona asociada
        person = SecurityRepository.get_person_by_id(user.person_id)

        # Obtener roles activos del usuario en una sola consulta JOIN SARGable
        active_roles = SecurityRepository.get_active_roles_for_user(user.id)
        role_names = [r.name for r in active_roles]

        return {
            "user_id": user.id,
            "username": user.username,
            "first_name": person.first_name if person else "",
            "last_name": person.last_name if person else "",
            "full_name": f"{person.first_name} {person.last_name}" if person else "",
            "email": (person.email or "") if person else "",
            "document_id": person.document_id if person else "",
            "roles": role_names,
            "created_at": person.created_at.isoformat() if person and hasattr(person, 'created_at') and person.created_at else None
        }

    # ── LOGOUT ────────────────────────────────────────────────────────────────
    @staticmethod
    def logout_user(jti: str, user_id: int, expires_at: datetime) -> dict:
        """Revoca el JWT actual agregándolo a la blacklist."""
        with transactional_session():
            if not SecurityRepository.is_token_blacklisted(jti):
                token = BlacklistedToken(
                    jti=jti,
                    user_id=user_id,
                    expires_at=expires_at
                )
                SecurityRepository.add_token_to_blacklist(token, commit=False)
        return {"message": "Sesión cerrada correctamente"}

    @staticmethod
    def forgot_password(identifier: str) -> dict:
        """Genera un token real y lo almacena para recuperar la contraseña."""
        user = SecurityRepository.get_user_by_identifier(identifier)
        if not user or not user.is_active:
            raise ValueError("Usuario no encontrado")
            
        import secrets
        import hashlib
        from datetime import timedelta
        
        # 1. Generar token criptográficamente seguro
        raw_token = secrets.token_urlsafe(32)
        
        # 2. Hashearlo para guardar en DB (por si la DB se compromete, los tokens no son usables)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # 3. Guardar en BD dentro de transacción ACID
        from app.core_security.models import PasswordResetToken
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        with transactional_session():
            token_record = PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
            SecurityRepository.create_password_reset_token(token_record, commit=False)
        
        # 4. Simulación del envío de correo (preparado para integrar SMTP)
        person = SecurityRepository.get_person_by_id(user.person_id)
        email_dest = person.email if person and person.email else f"{user.username}@colegio.edu.co"
        
        # SEG-08: En producción o cuando ENABLE_DEV_TOKEN sea falso, NUNCA se expone
        # el token en la respuesta pública de la API.
        from config import IS_PRODUCTION
        import os
        enable_dev_token = (
            not IS_PRODUCTION and 
            os.getenv('ENABLE_DEV_TOKEN', 'true').lower() == 'true'
        )
        
        response = {
            "message": f"Instrucciones de recuperación enviadas a {email_dest}"
        }
        if enable_dev_token:
            response["dev_token"] = raw_token  # Exclusivo para desarrollo/pruebas locales controladas
            
        return response

    @staticmethod
    def reset_password(raw_token: str, new_password: str) -> dict:
        import hashlib
        
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        with transactional_session():
            # Bloqueo pesimista SELECT ... FOR UPDATE para evitar consumo concurrente del mismo token
            token_record = SecurityRepository.get_password_reset_token_for_update(token_hash)
            
            if not token_record:
                raise ValueError("El token de recuperación es inválido.")
                
            if token_record.is_used:
                raise ValueError("Este token ya fue utilizado.")
                
            if token_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                raise ValueError("El token ha expirado.")
                
            user = SecurityRepository.get_user_by_id(token_record.user_id)
            if not user or not user.is_active:
                raise ValueError("El usuario asociado al token no es válido.")
                
            # Actualizar contraseña, marcar token e invalidar cualquier remanente activo en 1 sentencia SARGable
            user.password_hash = generate_password_hash(new_password)
            token_record.is_used = True
            SecurityRepository.invalidate_active_reset_tokens(user.id)
        
        return {"message": "La contraseña ha sido actualizada exitosamente."}

    # ── ROLES ─────────────────────────────────────────────────────────────────
    @staticmethod
    def create_role(name: str, description: str = None) -> dict:
        existing = SecurityRepository.get_role_by_name(name)
        if existing and existing.is_active:
            raise ValueError(f"El rol '{name}' ya existe")
        with transactional_session():
            if existing and not existing.is_active:
                existing.is_active = True
                if description is not None:
                    existing.description = description
                created = existing
            else:
                role = Role(name=name, description=description)
                created = SecurityRepository.create_role(role, commit=False)
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
        with transactional_session():
            role = SecurityRepository.get_role_by_id(role_id)
            if not role or not role.is_active:
                raise ValueError("Rol no encontrado o ya inactivo")
            role.is_active = False
        return {"message": f"Rol {role_id} desactivado (Soft Delete)"}

    # ── PERMISOS ──────────────────────────────────────────────────────────────
    @staticmethod
    def create_permission(name: str, description: str = None) -> dict:
        existing = SecurityRepository.get_permission_by_name(name)
        if existing and existing.is_active:
            raise ValueError(f"El permiso '{name}' ya existe")
        with transactional_session():
            if existing and not existing.is_active:
                existing.is_active = True
                if description is not None:
                    existing.description = description
                created = existing
            else:
                permission = Permission(name=name, description=description)
                created = SecurityRepository.create_permission(permission, commit=False)
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
        with transactional_session():
            p = SecurityRepository.get_permission_by_id(permission_id)
            if not p or not p.is_active:
                raise ValueError("Permiso no encontrado o ya inactivo")
            p.is_active = False
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

        existing = SecurityRepository.get_user_role_any(user_id, role_id)
        if existing and existing.is_active:
            raise ValueError("El usuario ya tiene ese rol asignado")

        with transactional_session():
            if existing and not existing.is_active:
                existing.is_active = True
            else:
                user_role = UserHasRole(user_id=user_id, role_id=role_id)
                SecurityRepository.assign_role_to_user(user_role, commit=False)
        return {
            "message": f"Rol '{role.name}' asignado al usuario '{user.username}'",
            "user_id": user_id,
            "role_id": role_id
        }

    @staticmethod
    def revoke_role_from_user(user_id: int, role_id: int) -> dict:
        with transactional_session():
            user_role = SecurityRepository.get_user_role(user_id, role_id)
            if not user_role:
                raise ValueError("El usuario no tiene ese rol asignado")
            user_role.is_active = False
        return {"message": "Rol revocado correctamente"}

    @staticmethod
    def get_user_roles(user_id: int) -> list:
        user = SecurityRepository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("Usuario no encontrado o inactivo")
        active_roles = SecurityRepository.get_active_roles_for_user(user_id)
        return [
            {"id": role.id, "name": role.name, "description": role.description}
            for role in active_roles
        ]

    # ── ASIGNACIÓN PERMISO → ROL ──────────────────────────────────────────────
    @staticmethod
    def assign_permission_to_role(role_id: int, permission_id: int) -> dict:
        role = SecurityRepository.get_role_by_id(role_id)
        if not role or not role.is_active:
            raise ValueError("Rol no encontrado o inactivo")

        permission = SecurityRepository.get_permission_by_id(permission_id)
        if not permission or not permission.is_active:
            raise ValueError("Permiso no encontrado o inactivo")

        existing = SecurityRepository.get_role_permission_any(role_id, permission_id)
        if existing and existing.is_active:
            raise ValueError("El rol ya tiene ese permiso asignado")

        with transactional_session():
            if existing and not existing.is_active:
                existing.is_active = True
            else:
                rhp = RoleHasPermission(role_id=role_id, permission_id=permission_id)
                SecurityRepository.assign_permission_to_role(rhp, commit=False)
        return {
            "message": f"Permiso '{permission.name}' asignado al rol '{role.name}'",
            "role_id": role_id,
            "permission_id": permission_id
        }

    @staticmethod
    def revoke_permission_from_role(role_id: int, permission_id: int) -> dict:
        with transactional_session():
            rhp = SecurityRepository.get_role_permission(role_id, permission_id)
            if not rhp:
                raise ValueError("El rol no tiene ese permiso asignado")
            rhp.is_active = False
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
        return SecurityRepository.get_all_users_enriched()

    @staticmethod
    def soft_delete_user(user_id: int) -> dict:
        with transactional_session():
            user = SecurityRepository.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise ValueError("Usuario no encontrado o ya inactivo")
            user.is_active = False
        return {"message": f"Usuario {user_id} desactivado (Soft Delete)"}
    
    @staticmethod
    def update_user_profile(user_id: int, data: dict) -> dict:
        with transactional_session():
            user = SecurityRepository.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise ValueError("Usuario no encontrado o inactivo")
            
            person = SecurityRepository.get_person_by_id(user.person_id)
            if person:
                if 'first_name' in data and data['first_name']:
                    person.first_name = data['first_name'].strip()
                if 'last_name' in data and data['last_name']:
                    person.last_name = data['last_name'].strip()
                if 'document_id' in data and data['document_id']:
                    validated_doc = validate_document_id(data['document_id'])
                    existing = SecurityRepository.get_person_by_document(validated_doc)
                    if existing and existing.id != person.id:
                        raise ValueError("Ya existe una persona registrada con ese documento de identidad")
                    person.document_id = validated_doc
                if 'email' in data and data['email']:
                    person.email = data['email'].strip()
                
            if 'role_name' in data and data['role_name']:
                role = SecurityRepository.get_role_by_name(data['role_name'])
                if not role or not role.is_active:
                    raise ValueError(f"El rol '{data['role_name']}' no existe o está inactivo.")
                
                # Remove existing role assignments
                UserHasRole.query.filter_by(user_id=user_id).delete()
                
                # Insert the new role assignment
                new_role = UserHasRole(user_id=user_id, role_id=role.id)
                db.session.add(new_role)
                
        return {"message": "Perfil de usuario actualizado exitosamente"}

    @staticmethod
    def update_own_profile(user_id: int, data: dict) -> dict:
        """Permite a cualquier usuario autenticado actualizar únicamente sus propios datos personales."""
        with transactional_session():
            user = SecurityRepository.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise ValueError("Usuario no encontrado o inactivo")
            
            person = SecurityRepository.get_person_by_id(user.person_id)
            if not person:
                raise ValueError("Datos de persona no encontrados para este usuario")
            
            if 'first_name' in data and data['first_name']:
                person.first_name = data['first_name'].strip()
            if 'last_name' in data and data['last_name']:
                person.last_name = data['last_name'].strip()
            if 'email' in data and data['email']:
                person.email = data['email'].strip()
                
        return {"message": "Datos personales actualizados exitosamente"}
