from sqlalchemy import text
from .database import engine


def purge_db_with_sql():
    """
    Deja la BD en blanco usando SQL puro.
    - SQLite: PRAGMA OFF/ON + DELETE table por table, cada una por separado.
    - Postgres: TRUNCATE ... RESTART IDENTITY CASCADE.
    """
    if engine.dialect.name == "sqlite":
        with engine.begin() as conn:
            
            conn.exec_driver_sql("PRAGMA foreign_keys = OFF")
            conn.exec_driver_sql("DELETE FROM detalleventa")
            conn.exec_driver_sql("DELETE FROM venta")
            conn.exec_driver_sql("DELETE FROM inventario")
            conn.exec_driver_sql("DELETE FROM llanta")
            conn.exec_driver_sql("DELETE FROM cliente")
            conn.exec_driver_sql("DELETE FROM asesor")

            conn.exec_driver_sql("PRAGMA foreign_keys = ON")

        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("VACUUM")
        except Exception:
            pass

    else:
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
