
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables
load_dotenv()

# Database URL with automatic SQLite fallback
DATABASE_URL = os.getenv("DATABASE_URL")
USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() in ("true", "1")
engine = None

if not USE_SQLITE and DATABASE_URL and DATABASE_URL.startswith("postgresql"):
    try:
        from sqlalchemy import text
        # Attempt connection with a short timeout
        test_engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 2})
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine = test_engine
        print("[Database] Successfully connected to PostgreSQL.")
    except Exception as e:
        print(f"[Database] PostgreSQL connection failed ({e}). Falling back to local SQLite.")
        DATABASE_URL = "sqlite:///./personal_safety.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    DATABASE_URL = DATABASE_URL if (DATABASE_URL and DATABASE_URL.startswith("sqlite")) else "sqlite:///./personal_safety.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    print(f"[Database] Using local SQLite database: {DATABASE_URL}")

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