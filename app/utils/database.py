# app/utils/database.py
"""
Utilidades de gestión transaccional ACID para SQLAlchemy.

Garantiza atomicidad (Todo o Nada) en operaciones de escritura simples o
compuestas:
  - Un único `db.session.commit()` al cerrar el bloque transaccional externo.
  - Soporte reentrante: si una función transaccional invoca a otra o a un
    repositorio, las operaciones intermedias hacen `db.session.flush()` y
    delegan el `commit` final al bloque raíz.
  - `db.session.rollback()` automático e inmediato ante cualquier excepción de
    negocio o de base de datos, evitando estados `PendingRollbackError` en las
    conexiones del pool.
"""
from contextlib import contextmanager
from functools import wraps
from app.extensions import db


@contextmanager
def transactional_session():
    """Context manager reentrante para ejecutar una unidad de trabajo ACID."""
    depth = db.session.info.get("_tx_depth", 0)
    db.session.info["_tx_depth"] = depth + 1
    try:
        yield db.session
        if depth == 0:
            db.session.commit()
        else:
            db.session.flush()
    except Exception:
        db.session.info["_tx_depth"] = 0
        db.session.rollback()
        raise
    else:
        db.session.info["_tx_depth"] = depth


def persist_entity(entity, commit: bool = True):
    """Agrega una entidad a la sesión respetando el contexto transaccional activo.
    Si está dentro de `transactional_session()` (o `commit=False`), ejecuta `flush()`
    para asignar llaves primarias sin romper la atomicidad. Si se invoca de forma
    aislada con `commit=True`, confirma con protección de `rollback()`.
    """
    db.session.add(entity)
    if commit and db.session.info.get("_tx_depth", 0) == 0:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
    else:
        db.session.flush()
    return entity


def transactional(fn):
    """Decorador para envolver un método de servicio en una transacción ACID."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with transactional_session():
            return fn(*args, **kwargs)
    return wrapper
