import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() in ("true", "1")
APP_ENV = os.getenv("APP_ENV", "development").lower()

engine = None

# Explicit SQLite mode (local development)
if USE_SQLITE:

    DATABASE_URL = "sqlite:///./personal_safety.db"

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    print("[Database] Using SQLite.")

# PostgreSQL mode (Railway deployment)
elif DATABASE_URL:

    # Normalize older PostgreSQL URL format
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1
        )

    # Explicitly select Psycopg 2
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql://",
            "postgresql+psycopg2://",
            1
        )

    # Handle URLs already specifying Psycopg 3
    elif DATABASE_URL.startswith("postgresql+psycopg://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql+psycopg://",
            "postgresql+psycopg2://",
            1
        )

    engine = create_engine(
        DATABASE_URL,
        connect_args={"connect_timeout": 5}
        if DATABASE_URL.startswith("postgresql")
        else {}
    )

    # Verify database connection
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        print("[Database] Successfully connected to PostgreSQL.")

    except Exception as e:
        engine.dispose()

        raise RuntimeError(
            f"[Database] PostgreSQL connection failed: {e}"
        ) from e

# Local fallback when no database URL is configured
elif APP_ENV != "production":

    DATABASE_URL = "sqlite:///./personal_safety.db"

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    print("[Database] Using local SQLite.")

# Production must have a configured database
else:

    raise RuntimeError(
        "[Database] DATABASE_URL is missing in production."
    )


# Create database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for database models
Base = declarative_base()

IS_SQLITE = DATABASE_URL.startswith("sqlite")


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()