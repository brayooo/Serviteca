import os
from sqlmodel import SQLModel, create_engine, Session, text
from sqlalchemy.pool import QueuePool
from typing import Generator
from dotenv import load_dotenv

load_dotenv()


def get_database_url() -> str:
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "serviteca")

    if not all([db_password, db_host]):
        raise ValueError("❌ Variables de entorno faltantes: DB_PASSWORD, DB_HOST")

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


DATABASE_URL = get_database_url()

# Configuración del engine PostgreSQL
engine = create_engine(
    DATABASE_URL,
    echo=False,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "options": "-c timezone=America/Bogota"
    }
)


def init_db():
    """Crea todas las tablas en la base de datos"""
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ Tablas creadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False


def get_session() -> Generator[Session, None, None]:
    """Generador de sesiones de base de datos"""
    with Session(engine) as session:
        yield session


def test_connection() -> bool:
    """Prueba la conexión y muestra información de la BD"""
    try:
        with Session(engine) as session:
            result = session.exec(text("SELECT version()")).first()
            print(f"✅ PostgreSQL conectado: {result[:60]}...")
            return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False