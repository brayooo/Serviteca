# app/admin.py
from sqlalchemy import text
from .database import engine


def purge_db_with_sql():
    """
    Deja la BD en blanco usando SQL puro.
    - SQLite: PRAGMA OFF/ON + DELETE table por table, cada una por separado.
    - Postgres: TRUNCATE ... RESTART IDENTITY CASCADE.
    """
    if engine.dialect.name == "sqlite":
        # 1) Ejecutar los DELETEs dentro de UNA transacción
        with engine.begin() as conn:
            # PRAGMA es por conexión; se aplica a esta
            conn.exec_driver_sql("PRAGMA foreign_keys = OFF")

            # Orden seguro (hijas -> padres). Una sentencia por llamada:
            conn.exec_driver_sql("DELETE FROM detalleventa")
            conn.exec_driver_sql("DELETE FROM venta")
            conn.exec_driver_sql("DELETE FROM inventario")
            conn.exec_driver_sql("DELETE FROM llanta")
            conn.exec_driver_sql("DELETE FROM cliente")
            conn.exec_driver_sql("DELETE FROM asesor")

            conn.exec_driver_sql("PRAGMA foreign_keys = ON")

        # 2) VACUUM debe ejecutarse FUERA de la transacción
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("VACUUM")
        except Exception:
            # Ignora si el motor no soporta VACUUM o hay bloqueo
            pass

    else:
        # Postgres / Supabase, etc.
        with engine.begin() as conn:
            conn.execute(text("""
                TRUNCATE TABLE
                  detalleventa,
                  venta,
                  inventario,
                  llanta,
                  cliente,
                  asesor
                RESTART IDENTITY CASCADE
            """))
