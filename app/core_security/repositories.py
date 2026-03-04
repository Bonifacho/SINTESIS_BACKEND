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