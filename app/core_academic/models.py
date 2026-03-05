from app.extensions import db
from datetime import datetime, timezone

class Group(db.Model):
    """Grupos o Clases (Ej: Grado 10-A)"""
    __tablename__ = 'academic_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Llave foránea hacia el usuario que es el profesor
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    enrollments = db.relationship('Enrollment', backref='group', lazy='dynamic', cascade="all, delete-orphan")
    topics = db.relationship('Topic', backref='group', lazy='dynamic', cascade="all, delete-orphan")

class Enrollment(db.Model):
    """Tabla pivote para matricular estudiantes en grupos"""
    __tablename__ = 'academic_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('academic_groups.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

class Topic(db.Model):
    __tablename__ = 'academic_topics'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('academic_groups.id'), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    
    # NUEVO: Soft Delete
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    lessons = db.relationship('Lesson', backref='topic', lazy='dynamic', cascade="all, delete-orphan")

class Lesson(db.Model):
    __tablename__ = 'academic_lessons'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('academic_topics.id'), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    
    # NUEVO: Soft Delete
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    activities = db.relationship('Activity', backref='lesson', lazy='dynamic', cascade="all, delete-orphan")

class Activity(db.Model):
    __tablename__ = 'academic_activities'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('academic_lessons.id'), nullable=False)
    ui_config = db.Column(db.JSON, nullable=False)
    passing_score = db.Column(db.Integer, default=80)
    order_index = db.Column(db.Integer, default=0)
    
    # NUEVO: Soft Delete
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
class StudentProgress(db.Model):
    """Registro de progreso tipo Duolingo"""
    __tablename__ = 'academic_student_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    # Llave foránea hacia el estudiante (User)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Llave foránea hacia la actividad
    activity_id = db.Column(db.Integer, db.ForeignKey('academic_activities.id'), nullable=False)
    
    score = db.Column(db.Integer, nullable=False) # Puntaje obtenido (ej. 100)
    passed = db.Column(db.Boolean, default=False) # ¿Superó el passing_score?
    completed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True, nullable=False)