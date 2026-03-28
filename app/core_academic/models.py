# app/core_academic/models.py
from app.extensions import db
from datetime import datetime, timezone
import enum


# ─────────────────────────────────────────────────────────────────────────────
# ENUM para tipos de recurso del OVA
# ─────────────────────────────────────────────────────────────────────────────
class ResourceType(enum.Enum):
    pdf    = "pdf"
    video  = "video"
    link   = "link"
    text   = "text"


# ─────────────────────────────────────────────────────────────────────────────
# CAPA 1 — Estructura académica (conservadas / ajustadas)
# ─────────────────────────────────────────────────────────────────────────────

class Group(db.Model):
    """Grupos o clases (ej: Grado 10-A). Asignados a un docente."""
    __tablename__ = 'academic_groups'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active  = db.Column(db.Boolean, default=True, nullable=False)

    # Relaciones
    enrollments = db.relationship('Enrollment', backref='group', lazy='dynamic', cascade="all, delete-orphan")
    topics      = db.relationship('Topic', backref='group', lazy='dynamic', cascade="all, delete-orphan")


class Enrollment(db.Model):
    """Matrícula de un estudiante en un grupo."""
    __tablename__ = 'academic_enrollments'

    id          = db.Column(db.Integer, primary_key=True)
    group_id    = db.Column(db.Integer, db.ForeignKey('academic_groups.id'), nullable=False)
    student_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active   = db.Column(db.Boolean, default=True, nullable=False)


class Topic(db.Model):
    """Tema dentro de un grupo (ej: Unidad 1 — Álgebra Lineal)."""
    __tablename__ = 'academic_topics'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(150), nullable=False)
    group_id    = db.Column(db.Integer, db.ForeignKey('academic_groups.id'), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)

    # Relaciones
    ovas = db.relationship('OVA', backref='topic', lazy='dynamic', cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────────────
# CAPA 2 — Contenedor OVA y sus recursos (nuevas)
# ─────────────────────────────────────────────────────────────────────────────

class OVA(db.Model):
    """
    Objeto Virtual de Aprendizaje. Es la unidad central de contenido.
    Reemplaza a Lesson + Activity. Solo almacena metadatos descriptivos —
    los recursos van en OVAResource y el motor de evaluación en Exam.
    """
    __tablename__ = 'academic_ovas'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    topic_id    = db.Column(db.Integer, db.ForeignKey('academic_topics.id'), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relaciones
    resources = db.relationship('OVAResource', backref='ova', lazy='dynamic', cascade="all, delete-orphan")
    exam      = db.relationship('Exam', backref='ova', uselist=False, cascade="all, delete-orphan")


class OVAResource(db.Model):
    """
    Recurso de estudio de un OVA (PDF, video, enlace o texto enriquecido).
    Normaliza lo que antes era el blob ui_config de Activity.
    El campo resource_type le dice al frontend cómo renderizar el recurso.
    """
    __tablename__ = 'academic_ova_resources'

    id            = db.Column(db.Integer, primary_key=True)
    ova_id        = db.Column(db.Integer, db.ForeignKey('academic_ovas.id'), nullable=False)
    resource_type = db.Column(db.Enum(ResourceType), nullable=False)
    url           = db.Column(db.String(500), nullable=True)   # para pdf / video / link
    content       = db.Column(db.Text, nullable=True)          # para text enriquecido
    display_title = db.Column(db.String(150), nullable=False)
    order_index   = db.Column(db.Integer, default=0)
    is_active     = db.Column(db.Boolean, default=True, nullable=False)


# ─────────────────────────────────────────────────────────────────────────────
# CAPA 3 — Motor de examen: catálogo (nuevas)
# ─────────────────────────────────────────────────────────────────────────────

class Exam(db.Model):
    """
    Examen asociado a un OVA. Un OVA puede tener 0 o 1 examen.
    Define la configuración global: umbral de aprobación y máximo de intentos.
    La docente configura max_attempts a voluntad (1 = formal, 999 = ilimitado).
    """
    __tablename__ = 'exam_exams'

    id           = db.Column(db.Integer, primary_key=True)
    ova_id       = db.Column(db.Integer, db.ForeignKey('academic_ovas.id'), nullable=False, unique=True)
    title        = db.Column(db.String(150), nullable=False)
    passing_score = db.Column(db.Integer, default=60, nullable=False)  # porcentaje mínimo para aprobar
    max_attempts  = db.Column(db.Integer, default=3, nullable=False)   # configurable por la docente
    is_active     = db.Column(db.Boolean, default=True, nullable=False)

    # Relaciones
    questions = db.relationship('Question', backref='exam', lazy='dynamic', cascade="all, delete-orphan")
    attempts  = db.relationship('ExamAttempt', backref='exam', lazy='dynamic', cascade="all, delete-orphan")


class Question(db.Model):
    """
    Pregunta del catálogo. NO contiene ninguna referencia a la respuesta
    correcta — esa información vive exclusivamente en AnswerKey.
    """
    __tablename__ = 'exam_questions'

    id          = db.Column(db.Integer, primary_key=True)
    exam_id     = db.Column(db.Integer, db.ForeignKey('exam_exams.id'), nullable=False)
    statement   = db.Column(db.Text, nullable=False)
    points      = db.Column(db.Integer, default=1, nullable=False)
    order_index = db.Column(db.Integer, default=0)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)

    # Relaciones
    options    = db.relationship('Option', backref='question', lazy='dynamic', cascade="all, delete-orphan")
    answer_key = db.relationship('AnswerKey', backref='question', uselist=False, cascade="all, delete-orphan")


class Option(db.Model):
    """
    Opción de respuesta para una pregunta. NO tiene campo is_correct —
    la corrección es responsabilidad exclusiva de AnswerKey.
    """
    __tablename__ = 'exam_options'

    id          = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('exam_questions.id'), nullable=False)
    text        = db.Column(db.String(500), nullable=False)
    order_index = db.Column(db.Integer, default=0)
    is_active   = db.Column(db.Boolean, default=True, nullable=False)


class AnswerKey(db.Model):
    """
    Clave de respuestas correctas. Tabla privilegiada — NUNCA se expone
    en ninguna ruta pública de la API. Solo el ExamService la consulta
    internamente al momento de calcular el resultado de un intento.
    """
    __tablename__ = 'exam_answer_key'

    id                = db.Column(db.Integer, primary_key=True)
    question_id       = db.Column(db.Integer, db.ForeignKey('exam_questions.id'), nullable=False, unique=True)
    correct_option_id = db.Column(db.Integer, db.ForeignKey('exam_options.id'), nullable=False)
    is_active         = db.Column(db.Boolean, default=True, nullable=False)


# ─────────────────────────────────────────────────────────────────────────────
# CAPA 4 — Huella transaccional (nuevas)
# ─────────────────────────────────────────────────────────────────────────────

class ExamAttempt(db.Model):
    """
    Metadatos de un intento de examen. Registra quién, cuándo empezó
    y cuándo envió. NO almacena score ni passed — esos valores se
    calculan al vuelo en el backend cuando el frontend los solicita.
    """
    __tablename__ = 'exam_attempts'

    id           = db.Column(db.Integer, primary_key=True)
    exam_id      = db.Column(db.Integer, db.ForeignKey('exam_exams.id'), nullable=False)
    student_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    started_at   = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    submitted_at = db.Column(db.DateTime, nullable=True)   # None = intento en curso
    is_active    = db.Column(db.Boolean, default=True, nullable=False)

    # Relaciones
    answers = db.relationship('AttemptAnswer', backref='attempt', lazy='dynamic', cascade="all, delete-orphan")


class AttemptAnswer(db.Model):
    """
    Huella inmutable del intento. Por cada pregunta del examen registra
    exactamente qué opción eligió el estudiante y a qué hora.
    Esta tabla NUNCA se modifica ni se borra físicamente.
    """
    __tablename__ = 'exam_attempt_answers'

    id                 = db.Column(db.Integer, primary_key=True)
    attempt_id         = db.Column(db.Integer, db.ForeignKey('exam_attempts.id'), nullable=False)
    question_id        = db.Column(db.Integer, db.ForeignKey('exam_questions.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('exam_options.id'), nullable=False)
    answered_at        = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active          = db.Column(db.Boolean, default=True, nullable=False)