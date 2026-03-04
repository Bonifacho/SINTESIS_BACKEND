# CONTEXTO DEL PROYECTO: SÍNTESIS (MVP)
**Sistema INtegral Tecnológico para la Enseñanza y el Seguimiento Interactivo Secuencial.**
Eres un AI Coding Assistant trabajando en SÍNTESIS, un LMS dinámico para una Escuela Normal Superior. 
Tu objetivo es ayudar a desarrollar el backend del MVP priorizando código limpio, escalable y ceñido a las reglas arquitectónicas descritas abajo.

## STACK TECNOLÓGICO
- **Backend:** Python 3.12+, Flask.
- **Gestor de Paquetes:** `uv` (Uso estricto de `uv add` y `uv run`, sin entornos virtuales clásicos).
- **ORM & BD:** SQLAlchemy, Flask-Migrate (Alembic), MariaDB.
- **Arquitectura:** Clean Architecture, patrón Repository/Service, Blueprints por dominio (`core_security` y `core_academic`).

## MANDAMIENTOS ESTRICTOS (REGLAS DE GENERACIÓN DE CÓDIGO)
Si vas a generar o modificar código, DEBES cumplir con lo siguiente:

1. **SEPARACIÓN DE DOMINIOS:** El sistema tiene dos núcleos principales totalmente desacoplados:
   - `core_security`: Modelos RBAC (`Person`, `User`, `Role`, `Permissions`).
   - `core_academic`: Modelos de LMS (`Group`, `Topic`, `Lesson`, `Activity`, `Progress`).
   NO mezcles lógica académica en el dominio de seguridad.

2. **REGLA DE ORO (CRUD TOTAL):**
   Toda entidad en la base de datos (por pequeña que sea) debe tener su controlador con rutas CRUD completas (GET, POST, PUT, DELETE) en la API.

3. **MIGRACIONES CODE-FIRST (PROHIBIDO SQL MANUAL):**
   Nunca generes scripts `ALTER TABLE` o `CREATE TABLE` en SQL crudo. Todo cambio estructural debe hacerse modificando los modelos de SQLAlchemy. Asume que el desarrollador ejecutará `uv run flask db migrate` y `uv run flask db upgrade`.

4. **AGNOSTICISMO DEL CONTENIDO (JSON POLIMÓRFICO):**
   El sistema no debe saber qué materia se está dictando. La interactividad de las actividades se maneja mediante un campo `ui_config` (tipo JSON) en la base de datos.
   - NUNCA hagas hardcode de IDs, nombres de materias, o tipos de preguntas en el código Python.
   - Los servicios deben validar que el JSON sea un diccionario válido, pero la estructura interna la dicta el frontend.

5. **NORMALIZACIÓN ESTRICTA (3FN):**
   Las relaciones en SQLAlchemy deben reflejar una base de datos en Tercera Forma Normal o superior. Usa claves foráneas claras y carga diferida estratégica para evitar problemas de rendimiento N+1.

6. **ENFOQUE EN EL MVP:**
   Limítate a construir la base descrita. Si se te pide una característica fuera del alcance base, advierte que pertenece a la Fase 2 y no escribas lógica compleja para ello.