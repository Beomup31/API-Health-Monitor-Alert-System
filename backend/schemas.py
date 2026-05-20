from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- Auth Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str

class UserBase(BaseModel):
    username: str

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- PingLog Schemas ---

class PingLogBase(BaseModel):
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    is_success: bool
    timestamp: datetime

class PingLog(PingLogBase):
    id: int
    endpoint_id: int

    model_config = ConfigDict(from_attributes=True)

# --- Endpoint Schemas ---

class EndpointBase(BaseModel):
    name: str
    url: HttpUrl
    expected_status: int = 200
    check_interval_minutes: int = 1

class EndpointCreate(EndpointBase):
    """Schema for creating a new endpoint (inherits all fields from EndpointBase)"""
    pass

class Endpoint(EndpointBase):
    """Schema for reading an endpoint (includes DB-generated ID)"""
    id: int
    
    # In Pydantic v2, from_attributes replaces orm_mode to allow reading from SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)