from app.extensions import db
from app.core_security.models import User, Person, Role

class SecurityRepository:
    @staticmethod
    def get_role_by_name(name: str) -> Role:
        return db.session.query(Role).filter_by(name=name).first()

    @staticmethod
    def create_role(role: Role) -> Role:
        db.session.add(role)
        db.session.commit()
        return role

    @staticmethod
    def create_user_and_person(person: Person, user: User) -> User:
        # Usamos flush() para que la BD nos genere el ID de la persona 
        # sin cerrar la transacción, permitiendo enlazarla al usuario.
        db.session.add(person)
        db.session.flush() 
        
        user.person_id = person.id
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def get_user_by_username(username: str) -> User:
        return db.session.query(User).filter_by(username=username).first()

    # ==========================================
    # REPOSITORIO DE ROLES
    # ==========================================
    @staticmethod
    def get_all_roles():
        """Obtiene todos los roles activos."""
        return db.session.query(Role).filter_by(is_active=True).all()

    @staticmethod
    def get_role_by_id(role_id: int) -> Role:
        """Obtiene un rol por su ID."""
        return db.session.query(Role).filter_by(id=role_id).first()

    # ==========================================
    # REPOSITORIO DE PERSONAS
    # ==========================================
    @staticmethod
    def get_all_persons():
        """Obtiene todas las personas activas."""
        return db.session.query(Person).filter_by(is_active=True).all()

    @staticmethod
    def get_person_by_id(person_id: int) -> Person:
        """Obtiene una persona por su ID."""
        return db.session.query(Person).filter_by(id=person_id).first()

    # ==========================================
    # REPOSITORIO DE USUARIOS
    # ==========================================
    @staticmethod
    def get_all_users():
        """Obtiene todos los usuarios activos."""
        return db.session.query(User).filter_by(is_active=True).all()

    @staticmethod
    def get_user_by_id(user_id: int) -> User:
        """Obtiene un usuario por su ID."""
        return db.session.query(User).filter_by(id=user_id).first()