from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Engine manages the connection pool to Postgres
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Each request gets its own session from this factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM models will inherit from this Base
Base = declarative_base()


def get_db():
    """
    Dependency function used by FastAPI's Depends().
    Ensures the DB session is always closed after the request,
    even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()