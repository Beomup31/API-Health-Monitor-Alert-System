from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Using SQLite for easy local setup. In a production environment, 
# this would typically be replaced by PostgreSQL or MySQL.
SQLALCHEMY_DATABASE_URL = "sqlite:///./health_monitor.db"

# check_same_thread=False is required for SQLite in FastAPI because 
# FastAPI can access the database from different worker threads.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# SessionLocal class will be used to create actual database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our SQLAlchemy models
Base = declarative_base()

def get_db():
    """
    Dependency function to get a database session for each request.
    Ensures the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
