# 🛡️ SÍNTESIS API — Backend RESTful (Flask & SQLAlchemy)

<div align="center">
  <img src="https://img.shields.io/badge/Estado-PRODUCCI%C3%93N_STABLE-success" alt="Estado" />
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue?logo=python" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/Framework-Flask_3.1-black?logo=flask" alt="Flask" />
  <img src="https://img.shields.io/badge/ORM-SQLAlchemy_2.0-red" alt="SQLAlchemy" />
  <img src="https://img.shields.io/badge/Database-MySQL%20%7C%20MariaDB-4479A1?logo=mysql" alt="Database" />
  <img src="https://img.shields.io/badge/Auth-JWT_RBAC-orange?logo=jsonwebtokens" alt="JWT" />
</div>

> **Sistema INtegral Tecnológico para la Enseñanza y el Seguimiento Interactivo Secuencial.**

Backend API centralizado para la plataforma educativa **SÍNTESIS**, estructurado bajo una arquitectura limpia y modular con separación estricta por dominios pedagógicos y de seguridad.

---

## 📑 Tabla de Contenidos

1. [Resumen Funcional y Arquitectura](#-resumen-funcional-y-arquitectura)
2. [Stack Tecnológico](#-stack-tecnológico)
3. [Estructura del Proyecto](#-estructura-del-proyecto)
4. [Modelo de Datos y Entidades](#-modelo-de-datos-y-entidades)
5. [Seguridad y Control de Acceso (RBAC)](#-seguridad-y-control-de-acceso-rbac)
6. [Catálogo de Endpoints](#-catálogo-de-endpoints)
7. [Instalación y Ejecución Local](#-instalación-y-ejecución-local)
8. [Despliegue y Producción](#-despliegue-y-producción)

---

## 🌟 Resumen Funcional y Arquitectura

La API implementa un modelo desacoplado basado en Blueprints de Flask y el patrón **Repository-Service-Controller**:

* **`core_security`**: Identidad, usuarios, personas naturales, roles y autenticación mediante JWT (Access & Refresh tokens).
* **`core_academic`**: Estructura curricular de grupos, matrículas, temas y el ecosistema completo de **OVAs (Objetos Virtuales de Aprendizaje)**, recursos pedagógicos multimedia y motor transaccional de evaluaciones.

---

## 🛠️ Stack Tecnológico

* **Lenguaje:** Python `>=3.12`
* **Framework:** Flask 3.1
* **ORM:** Flask-SQLAlchemy 3.1 & SQLAlchemy 2.0
* **Migraciones:** Alembic & Flask-Migrate
* **Conector de BD:** PyMySQL (MariaDB / MySQL)
* **Autenticación:** Flask-JWT-Extended 4.7
* **Servidor WSGI de Producción:** Gunicorn 25.3
* **CORS:** Flask-CORS 6.0
* **Gestión de Entorno:** python-dotenv 1.2

---

## 📂 Estructura del Proyecto

```text
SINTESIS_BACKEND/
├── app/
│   ├── __init__.py                # App Factory (create_app), blueprints y health checks
│   ├── extensions.py              # Inicialización de db, migrate, jwt y cors
│   │
│   ├── core_security/             # DOMINIO DE SEGURIDAD
│   │   ├── models.py              # Role, Person, User
│   │   ├── repositories.py        # Consultas SQL y persistencia
│   │   ├── services.py            # Hashing bcrypt, login, registro y tokens
│   │   └── routes.py              # Endpoints /api/v1/security
│   │
│   ├── core_academic/             # DOMINIO ACADÉMICO Y EVALUATIVO
│   │   ├── models.py              # Group, Topic, OVA, OVAResource, Exam, Question, Option, Attempt
│   │   ├── repositories.py        # Consultas de cursos, OVAs y respuestas
│   │   ├── services.py            # Lógica de negocio, cálculo de notas y snapshots
│   │   └── routes.py              # Endpoints /api/v1/academic
│   │
│   └── utils/
│       └── responses.py           # Helpers estándar para respuestas JSON
│
├── migrations/                    # Control de versiones del esquema (Alembic)
│   └── versions/                  # Revisiones históricas de la base de datos
├── config.py                      # Configuración dinámica (Dev, Test, Prod)
├── requirements.txt               # Dependencias fijadas para despliegue
├── pyproject.toml                 # Metadatos del paquete
├── run.py                         # Entrypoint de desarrollo local
└── README.md
```

---

## 🗄️ Modelo de Datos y Entidades

### 1. Dominio de Seguridad
* **`roles`**: Catálogo de roles del sistema (`administrador`, `docente`, `estudiante`, `practicante`).
* **`persons`**: Datos biográficos del usuario (nombres, apellidos, número de documento).
* **`users`**: Credenciales de acceso (`username`, `password_hash`), estado activo y llaves foráneas a `Person` y `Role`.

### 2. Dominio Académico
* **`academic_groups`**: Cursos o grupos asignados a un docente.
* **`academic_enrollments`**: Matrículas de estudiantes en grupos.
* **`academic_topics`**: Unidades pedagógicas o temas temáticos dentro de un grupo.
* **`academic_ovas`**: Objetos Virtuales de Aprendizaje que agrupan materiales y su prueba.
* **`academic_ova_resources`**: Recursos individuales de estudio:
  * `video` (reproductor nativo y URLs YouTube/Vimeo)
  * `pdf` (visores de documentos)
  * `link` (enlaces externos)
  * `text` (texto enriquecido markdown con tipografía ajustable)
* **`exam_exams`**: Configuración de la evaluación del OVA (`passing_score` %, `max_attempts`).
* **`exam_questions`**: Preguntas de opción múltiple con puntaje asignado.
* **`exam_options`**: Opciones de respuesta para cada pregunta.
* **`exam_answer_key`**: Clave de respuestas correctas (tabla protegida no accesible públicamente).
* **`exam_attempts`**: Huella inmutable de cada intento de evaluación (fecha, puntaje porcentual, cantidad de aciertos y estado de aprobación congelados al momento de entrega).

---

## 🔒 Seguridad y Control de Acceso (RBAC)

1. **Decorador `@role_required(*roles)`**:
   Protege las rutas a nivel de controlador exigiendo que el token JWT contenga los privilegios adecuados.
2. **Protección de Listado de Usuarios (SEG-04)**:
   La consulta general de usuarios (`GET /api/v1/security/users`) está restringida a administradores y docentes.
3. **Tablas Privilegiadas Ocultas**:
   La tabla `exam_answer_key` nunca se envía al cliente. La calificación se realiza de forma atómica en el servidor.
4. **Soft Delete**:
   Entidades principales preservan integridad referencial mediante el flag `is_active`.

---

## 📡 Catálogo de Endpoints Principales

### Seguridad (`/api/v1/security`)
| Método | Endpoint | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `POST` | `/login` | Autenticación y retorno de JWT | Público |
| `POST` | `/register` | Registro de usuario | Admin |
| `POST` | `/refresh` | Renovación de token expirado | Bearer Token |
| `GET` | `/users` | Listado general de usuarios | Admin, Docente |
| `GET` | `/users/<id>` | Detalle de usuario | Autenticado |
| `GET` | `/roles` | Listado de roles disponibles | Admin |

### Académico (`/api/v1/academic`)
| Método | Endpoint | Descripción | Acceso |
| :--- | :--- | :--- | :--- |
| `GET` | `/groups` | Grupos del docente o sistema | Docente, Admin |
| `POST` | `/groups` | Crear nuevo grupo | Docente, Admin |
| `GET` | `/groups/<id>/topics` | Temas asociados a un grupo | Autenticado |
| `POST` | `/topics` | Crear tema o unidad | Docente, Admin |
| `GET` | `/topics/<id>/ovas` | OVAs asociados a un tema | Autenticado |
| `POST` | `/ovas` | Crear nuevo OVA | Docente, Admin |
| `POST` | `/resources` | Asociar recurso multimedia a un OVA | Docente, Admin |
| `GET` | `/exams/by-ova/<id>/teacher` | Obtener examen con opciones (docente) | Docente, Admin |
| `GET` | `/exams/by-ova/<id>/student` | Obtener examen para rendir (sin respuestas) | Estudiante |
| `POST` | `/attempts` | Iniciar intento de examen | Estudiante |
| `POST` | `/attempts/<id>/submit` | Enviar respuestas y calificar intento | Estudiante |
| `GET` | `/attempts/<id>` | Obtener resultado detallado de intento | Autenticado |
| `GET` | `/groups/<id>/attempts` | Resultados de exámenes de un grupo | Docente, Admin |

---

## ⚙️ Instalación y Ejecución Local

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/Bonifacho/SINTESIS_BACKEND.git
   cd SINTESIS_BACKEND
   ```

2. **Crear y activar el entorno virtual**:
   ```bash
   python -m venv .venv
   # En Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar el archivo `.env`**:
   Crear un archivo `.env` en la raíz con las siguientes variables:
   ```env
   FLASK_APP=run.py
   FLASK_ENV=development
   DATABASE_URL=mysql+pymysql://usuario:password@localhost:3306/sintesis_db
   JWT_SECRET_KEY=tu_clave_secreta_jwt_muy_segura
   JWT_ACCESS_TOKEN_EXPIRES=86400
   PORT=5000
   ```

5. **Ejecutar migraciones**:
   ```bash
   flask db upgrade
   ```

6. **Iniciar el servidor de desarrollo**:
   ```bash
   python run.py
   ```
   La API quedará escuchando en `http://localhost:5000` con el health check en `/health`.

---

## 🚀 Despliegue y Producción

Este backend está optimizado para ejecutarse en plataformas en la nube como **Render** utilizando Gunicorn:

```bash
gunicorn "run:app" --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

---
*Desarrollado para el proyecto de grado SÍNTESIS (2026).*
