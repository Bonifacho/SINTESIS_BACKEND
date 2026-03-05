from werkzeug.security import generate_password_hash, check_password_hash
from app.core_security.models import User, Person, Role
from app.core_security.repositories import SecurityRepository
from app.extensions import db
from flask_jwt_extended import create_access_token


class SecurityService:
    @staticmethod
    def register_user(person_data: dict, user_data: dict, role_name: str) -> dict:
        # 1. Verificar el rol (Si estamos en MVP y no existe, lo creamos temporalmente)
        role = SecurityRepository.get_role_by_name(role_name)
        if not role:
            role = SecurityRepository.create_role(Role(name=role_name, description=f"Rol base: {role_name}"))

        # 2. Encriptar la contraseña (Regla de oro de seguridad)
        hashed_pw = generate_password_hash(user_data['password'])

        # 3. Construir las entidades (Modelos)
        new_person = Person(
            first_name=person_data['first_name'],
            last_name=person_data['last_name'],
            document_id=person_data['document_id']
        )

        new_user = User(
            username=user_data['username'],
            password_hash=hashed_pw,
            role_id=role.id,
            is_active=True
        )

        # 4. Delegar la persistencia al Repositorio
        created_user = SecurityRepository.create_user_and_person(new_person, new_user)

        # 5. Retornar DTO (Data Transfer Object) seguro para la API
        return {
            "id": created_user.id,
            "username": created_user.username,
            "role": role.name,
            "person": {
                "first_name": created_user.person.first_name,
                "last_name": created_user.person.last_name,
                "document_id": created_user.person.document_id
            }
        }
        
    @staticmethod
    def login(username: str, password: str) -> dict:
        # 1. Buscar al usuario en la base de datos
        user = SecurityRepository.get_user_by_username(username)
        
        # 2. Verificar que exista y que la contraseña coincida con el Hash
        if not user or not check_password_hash(user.password_hash, password):
            raise ValueError("Credenciales inválidas. Usuario o contraseña incorrectos.")

        # 3. Fabricar la "manilla VIP" (El Token). Guardamos su ID y su Rol adentro.
        access_token = create_access_token(
            identity=str(user.id), 
            additional_claims={"role": user.role.name}
        )

        return {
            "message": "Login exitoso",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role.name
            }
        }

    # ==========================================
    # CRUD DE ROLES
    # ==========================================
    @staticmethod
    def create_role(name: str, description: str = None) -> dict:
        """Crea un nuevo rol en el sistema."""
        existing = SecurityRepository.get_role_by_name(name)
        if existing:
            raise ValueError(f"Ya existe un rol con el nombre '{name}'")
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
        """Obtiene todos los roles activos."""
        roles = SecurityRepository.get_all_roles()
        return [{
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "is_active": r.is_active
        } for r in roles]

    @staticmethod
    def get_role_by_id(role_id: int) -> dict:
        """Obtiene un rol específico por su ID."""
        role = SecurityRepository.get_role_by_id(role_id)
        if not role or not role.is_active:
            raise ValueError("Rol no encontrado o inactivo")
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_active": role.is_active
        }

    @staticmethod
    def update_role(role_id: int, name: str = None, description: str = None) -> dict:
        """Actualiza los datos de un rol existente."""
        role = SecurityRepository.get_role_by_id(role_id)
        if not role or not role.is_active:
            raise ValueError("Rol no encontrado o inactivo")
        if name:
            role.name = name
        if description is not None:
            role.description = description
        db.session.commit()
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_active": role.is_active
        }

    @staticmethod
    def soft_delete_role(role_id: int) -> dict:
        """Desactiva un rol (Soft Delete)."""
        role = SecurityRepository.get_role_by_id(role_id)
        if not role or not role.is_active:
            raise ValueError("Rol no encontrado o ya estaba inactivo")
        role.is_active = False
        db.session.commit()
        return {"message": f"Rol {role_id} desactivado correctamente (Soft Delete)"}

    # ==========================================
    # CRUD DE PERSONAS
    # ==========================================
    @staticmethod
    def get_all_persons() -> list:
        """Obtiene todas las personas activas."""
        persons = SecurityRepository.get_all_persons()
        return [{
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "document_id": p.document_id,
            "is_active": p.is_active,
            "created_at": p.created_at.isoformat()
        } for p in persons]

    @staticmethod
    def get_person_by_id(person_id: int) -> dict:
        """Obtiene una persona específica por su ID."""
        person = SecurityRepository.get_person_by_id(person_id)
        if not person or not person.is_active:
            raise ValueError("Persona no encontrada o inactiva")
        return {
            "id": person.id,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "document_id": person.document_id,
            "is_active": person.is_active,
            "created_at": person.created_at.isoformat()
        }

    @staticmethod
    def update_person(person_id: int, data: dict) -> dict:
        """Actualiza los datos personales de una persona."""
        person = SecurityRepository.get_person_by_id(person_id)
        if not person or not person.is_active:
            raise ValueError("Persona no encontrada o inactiva")
        if 'first_name' in data:
            person.first_name = data['first_name']
        if 'last_name' in data:
            person.last_name = data['last_name']
        if 'document_id' in data:
            person.document_id = data['document_id']
        db.session.commit()
        return {
            "id": person.id,
            "first_name": person.first_name,
            "last_name": person.last_name,
            "document_id": person.document_id,
            "is_active": person.is_active
        }

    @staticmethod
    def soft_delete_person(person_id: int) -> dict:
        """Desactiva una persona (Soft Delete)."""
        person = SecurityRepository.get_person_by_id(person_id)
        if not person or not person.is_active:
            raise ValueError("Persona no encontrada o ya estaba inactiva")
        person.is_active = False
        db.session.commit()
        return {"message": f"Persona {person_id} desactivada correctamente (Soft Delete)"}

    # ==========================================
    # CRUD DE USUARIOS
    # ==========================================
    @staticmethod
    def get_all_users() -> list:
        """Obtiene todos los usuarios activos con su información."""
        users = SecurityRepository.get_all_users()
        return [{
            "id": u.id,
            "username": u.username,
            "is_active": u.is_active,
            "role": u.role.name,
            "person": {
                "first_name": u.person.first_name,
                "last_name": u.person.last_name,
                "document_id": u.person.document_id
            }
        } for u in users]

    @staticmethod
    def get_user_by_id(user_id: int) -> dict:
        """Obtiene un usuario específico por su ID."""
        user = SecurityRepository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("Usuario no encontrado o inactivo")
        return {
            "id": user.id,
            "username": user.username,
            "is_active": user.is_active,
            "role": user.role.name,
            "person": {
                "first_name": user.person.first_name,
                "last_name": user.person.last_name,
                "document_id": user.person.document_id
            }
        }

    @staticmethod
    def update_user(user_id: int, data: dict) -> dict:
        """Actualiza datos del usuario (contraseña y/o rol)."""
        user = SecurityRepository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("Usuario no encontrado o inactivo")
        if 'password' in data:
            user.password_hash = generate_password_hash(data['password'])
        if 'role' in data:
            role = SecurityRepository.get_role_by_name(data['role'])
            if not role:
                raise ValueError(f"Rol '{data['role']}' no encontrado")
            user.role_id = role.id
        db.session.commit()
        return {
            "id": user.id,
            "username": user.username,
            "is_active": user.is_active,
            "role": user.role.name
        }

    @staticmethod
    def soft_delete_user(user_id: int) -> dict:
        """Desactiva un usuario (Soft Delete)."""
        user = SecurityRepository.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("Usuario no encontrado o ya estaba inactivo")
        user.is_active = False
        db.session.commit()
        return {"message": f"Usuario {user_id} desactivado correctamente (Soft Delete)"}