from app.extensions import db
from app.core_academic.models import Group, Topic, Lesson, Activity

class AcademicRepository:
    @staticmethod
    def create_group(group: Group) -> Group:
        db.session.add(group)
        db.session.commit()
        return group
    
    @staticmethod
    def get_group_by_id(group_id: int) -> Group:
        return db.session.query(Group).filter_by(id=group_id).first()