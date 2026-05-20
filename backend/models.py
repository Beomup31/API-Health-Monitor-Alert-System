from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from database import Base

class User(Base):
    """
    SQLAlchemy model representing an admin user for authentication.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Endpoint(Base):
    """
    SQLAlchemy model representing an API endpoint to be monitored.
    """
    __tablename__ = "endpoints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String, nullable=False)
    expected_status = Column(Integer, default=200)
    check_interval_minutes = Column(Integer, default=1)

    # One-to-Many relationship with PingLog
    logs = relationship("PingLog", back_populates="endpoint", cascade="all, delete-orphan")


class PingLog(Base):
    """
    SQLAlchemy model representing a single health check result for an endpoint.
    """
    __tablename__ = "ping_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, ForeignKey("endpoints.id", ondelete="CASCADE"))
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    is_success = Column(Boolean, default=False)
    # Using timezone-aware UTC datetime for consistent time tracking
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Many-to-One relationship back to the Endpoint
    endpoint = relationship("Endpoint", back_populates="logs")