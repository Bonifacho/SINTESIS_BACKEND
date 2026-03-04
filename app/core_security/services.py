from werkzeug.security import generate_password_hash
from app.core_security.models import User, Person, Role
from app.core_security.repositories import SecurityRepository
from werkzeug.security import check_password_hash
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