# SÍNTESIS API (MVP)

Sistema INtegral Tecnológico para la Enseñanza y el Seguimiento Interactivo Secuencial.

Backend API en Flask para un LMS con separación por dominios:

- `core_security`: identidad, usuarios, roles y autenticación.
- `core_academic`: grupos, estructura pedagógica, matrícula y progreso.

---

## 1 Resumen funcional

Este proyecto implementa el MVP del backend de una plataforma educativa con:

- Registro y login con JWT.
- Gestión de entidades de seguridad (roles, personas, usuarios).
- Gestión académica (grupos, temas, lecciones, actividades, matrículas y progreso).
- Soft Delete por `is_active` en la mayoría de entidades.
- Migrations con Alembic / Flask-Migrate (enfoque code-first).

La aplicación expone dos blueprints principales:

- Seguridad: `/api/v1/security/...`
- Académico: `/api/v1/academic/...`

También tiene endpoints base de observabilidad:

- `GET /health`
- `GET /`

---

## 2 Stack tecnológico

- Python `>=3.12`
- Flask
- Flask-SQLAlchemy
- Flask-Migrate (Alembic)
- MariaDB/MySQL vía `PyMySQL`
- `python-dotenv`
- Werkzeug Security (`generate_password_hash`, `check_password_hash`)
- JWT (`flask-jwt-extended` usado en código)

Dependencias declaradas en `pyproject.toml`:

- `flask-migrate>=4.1.0`
- `flask-sqlalchemy>=3.1.1`
- `pymysql>=1.1.2`
- `python-dotenv>=1.2.1`

Dependencias bloqueadas (resueltas) en `uv.lock` incluyen, entre otras:

- `flask`, `sqlalchemy`, `alembic`, `werkzeug`, `jinja2`, `greenlet`.

---

## 3 Estructura del proyecto

```text
SINTESIS/
├── app/
│   ├── __init__.py                # App factory, registro de blueprints, health/index
│   ├── extensions.py              # db, migrate, jwt
│   ├── core_security/
│   │   ├── models.py              # Role, Person, User
│   │   ├── repositories.py        # Acceso a datos de seguridad
│   │   ├── services.py            # Lógica de negocio de seguridad
│   │   └── routes.py              # Endpoints /api/v1/security
│   ├── core_academic/
│   │   ├── models.py              # Group, Enrollment, Topic, Lesson, Activity, StudentProgress
│   │   ├── repositories.py        # Acceso a datos académicos
│   │   ├── services.py            # Lógica de negocio académica
│   │   └── routes.py              # Endpoints /api/v1/academic
│   └── utils/
│       └── responses.py           # (actualmente vacío)
├── migrations/
│   ├── env.py
│   ├── alembic.ini
│   └── versions/                  # Historial de revisiones de esquema
├── run.py                         # Punto de arranque principal de Flask
├── main.py                        # Script placeholder independiente
├── config.py                      # Configuración por variables de entorno
├── pyproject.toml                 # Metadatos y dependencias
├── uv.lock                        # Lock de dependencias
└── README.md
```

---

## 4 Arquitectura y responsabilidades

Patrón aplicado por dominio:

- **`models.py`**: definición ORM (estructura de tablas/relaciones).
- **`repositories.py`**: encapsula consultas y persistencia.
- **`services.py`**: reglas de negocio y validaciones.
- **`routes.py`**: capa HTTP (validación de payload, códigos de estado, respuestas JSON).

En `app/__init__.py`:

- Se crea la app (`create_app`).
- Se cargan configuraciones desde `Config`.
- Se inicializan extensiones (`db`, `migrate`, `jwt`).
- Se registran blueprints de seguridad y académico.

---

## 5 Modelo de datos

### 5.1 Dominio de seguridad

- **`roles`**
	- `id`, `name` (único), `description`, `is_active`
- **`persons`**
	- `id`, `first_name`, `last_name`, `document_id` (único), `created_at`, `is_active`
- **`users`**
	- `id`, `username` (único), `password_hash`, `is_active`, `person_id` (único FK), `role_id` (FK)

Relaciones:

- `Role 1:N User`
- `Person 1:1 User`

### 5.2 Dominio académico

- **`academic_groups`**
	- `id`, `name`, `teacher_id` (FK a `users`), `created_at`, `is_active`
- **`academic_enrollments`**
	- `id`, `group_id` (FK), `student_id` (FK a `users`), `enrolled_at`, `is_active`
- **`academic_topics`**
	- `id`, `title`, `group_id` (FK), `order_index`, `is_active`
- **`academic_lessons`**
	- `id`, `title`, `topic_id` (FK), `order_index`, `is_active`
- **`academic_activities`**
	- `id`, `title`, `lesson_id` (FK), `ui_config` (JSON), `passing_score`, `order_index`, `is_active`
- **`academic_student_progress`**
	- `id`, `student_id` (FK a `users`), `activity_id` (FK), `score`, `passed`, `completed_at`, `is_active`

Relaciones de contenido:

- `Group 1:N Topic`
- `Topic 1:N Lesson`
- `Lesson 1:N Activity`

---

## 6 Migraciones (Alembic)

Cadena detectada en `migrations/versions`:

1. `de0b79ce6bbc` → tablas RBAC iniciales (`persons`, `roles`, `users`)
2. `10c045cf3e6b` → tablas académicas base (`groups`, `enrollments`, `topics`, `lessons`, `activities`)
3. `fd5e672f2758` → `academic_student_progress`
4. `7687be996e9d` → `is_active` en `academic_groups`
5. `671eda77e5e6` → `is_active` en `academic_topics`, `academic_lessons`, `academic_activities`
6. `9f6c64d0700b` → `is_active` en `roles`, `persons`, `academic_enrollments`, `academic_student_progress`

Comandos típicos:

```bash
flask db migrate -m "mensaje"
flask db upgrade
```

---

## 7 Configuración de entorno

Variables esperadas en `.env`:

- `DATABASE_URL` (obligatoria para SQLAlchemy)
- `SECRET_KEY` (opcional; tiene valor por defecto)
- `JWT_SECRET_KEY` (opcional; tiene valor por defecto)

Ejemplo:

```env
DATABASE_URL=mysql+pymysql://usuario:password@localhost:3306/sintesis
SECRET_KEY=tu_secret_key
JWT_SECRET_KEY=tu_jwt_secret_key
```

---

## 8 Ejecución local

### Opción A (recomendada si usas `uv`)

```bash
uv sync
uv run python run.py
```

### Opción B (venv clásico)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -U pip
pip install flask flask-sqlalchemy flask-migrate flask-jwt-extended pymysql python-dotenv
python run.py
```

La API queda por defecto en `http://localhost:5000`.

---

## 9 Endpoints

### 9.1 Health

- `GET /health`
- `GET /`

### 9.2 Seguridad (`/api/v1/security`)

Autenticación:

- `POST /register`
- `POST /login`

Roles:

- `POST /roles` (JWT)
- `GET /roles` (JWT)
- `GET /roles/<role_id>` (JWT)
- `PUT /roles/<role_id>` (JWT)
- `DELETE /roles/<role_id>` (JWT, soft delete)

Personas:

- `GET /persons` (JWT)
- `GET /persons/<person_id>` (JWT)
- `PUT /persons/<person_id>` (JWT)
- `DELETE /persons/<person_id>` (JWT, soft delete)

Usuarios:

- `GET /users` (JWT)
- `GET /users/<user_id>` (JWT)
- `PUT /users/<user_id>` (JWT)
- `DELETE /users/<user_id>` (JWT, soft delete)

### 9.3 Académico (`/api/v1/academic`)

Grupos y árbol de contenido:

- `POST /groups`
- `POST /build-tree`
- `GET /groups/<group_id>/course` (JWT)
- `PUT /groups/<group_id>` (JWT)
- `DELETE /groups/<group_id>` (JWT, soft delete)

Temas:

- `PUT /topics/<topic_id>` (JWT)
- `DELETE /topics/<topic_id>` (JWT, soft delete)

Lecciones:

- `PUT /lessons/<lesson_id>` (JWT)
- `DELETE /lessons/<lesson_id>` (JWT, soft delete)

Actividades:

- `PUT /activities/<activity_id>` (JWT)
- `DELETE /activities/<activity_id>` (JWT, soft delete)

Matrículas:

- `POST /enrollments` (JWT)
- `GET /groups/<group_id>/enrollments` (JWT)
- `GET /enrollments/<enrollment_id>` (JWT)
- `PUT /enrollments/<enrollment_id>` (JWT)
- `DELETE /enrollments/<enrollment_id>` (JWT, soft delete)

Progreso:

- `POST /progress`
- `GET /progress/student/<student_id>` (JWT)
- `GET /progress/<progress_id>` (JWT)
- `PUT /progress/<progress_id>` (JWT)
- `DELETE /progress/<progress_id>` (JWT, soft delete)

---

## 10 Convenciones funcionales observadas

- Estrategia de **Soft Delete** generalizada (`is_active`).
- Contraseñas siempre almacenadas como hash.
- JWT con `identity=user.id` y `role` en claims adicionales.
- `ui_config` permite agnosticismo de actividades (el backend no fija estructura pedagógica rígida).

---

## 11 Notas de mantenimiento

- `main.py` es un script placeholder y no es el entrypoint real de la API.
- `app/utils/responses.py` existe pero está vacío.
- `flask-jwt-extended` se usa en código y conviene mantenerlo explícito en dependencias declaradas.

---

## 12 Estado del repositorio documentado

Este README fue elaborado a partir del contenido actual de:

- código fuente (`app/`, `run.py`, `config.py`, etc.),
- migraciones (`migrations/`),
- configuración y lock de dependencias (`pyproject.toml`, `uv.lock`),
- artefactos de contexto (`AGENTES.md`, `guion_video.txt`).


