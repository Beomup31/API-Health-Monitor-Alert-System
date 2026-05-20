from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from contextlib import asynccontextmanager

import models, schemas, crud, auth
from database import engine, get_db, SessionLocal
from scheduler import start_scheduler, stop_scheduler

# Initialize database tables. In production, consider using Alembic for migrations.
models.Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to handle startup and shutdown events.
    """
    # Create default admin user on startup if it doesn't exist
    db = SessionLocal()
    try:
        admin = crud.get_user_by_username(db, username="admin")
        if not admin:
            hashed_pw = auth.get_password_hash("admin123")
            db.add(models.User(username="admin", hashed_password=hashed_pw))
            db.commit()
    finally:
        db.close()

    # Startup: Start the background scheduler
    start_scheduler()
    yield
    # Shutdown: Stop the background scheduler
    stop_scheduler()

app = FastAPI(
    title="API Health Monitor & Alert System",
    description="Backend API for managing and monitoring API endpoints.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return a JWT token."""
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Protect all /endpoints routes with JWT dependency
@app.post("/endpoints/", response_model=schemas.Endpoint, status_code=status.HTTP_201_CREATED)
def create_endpoint(endpoint: schemas.EndpointCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.create_endpoint(db=db, endpoint=endpoint)

@app.get("/endpoints/", response_model=List[schemas.Endpoint])
def read_endpoints(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.get_endpoints(db, skip=skip, limit=limit)

@app.get("/endpoints/{endpoint_id}", response_model=schemas.Endpoint)
def read_endpoint(endpoint_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_endpoint = crud.get_endpoint(db, endpoint_id=endpoint_id)
    if db_endpoint is None:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return db_endpoint

@app.put("/endpoints/{endpoint_id}", response_model=schemas.Endpoint)
def update_endpoint(endpoint_id: int, endpoint: schemas.EndpointCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_endpoint = crud.update_endpoint(db, endpoint_id=endpoint_id, endpoint=endpoint)
    if db_endpoint is None:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return db_endpoint

@app.delete("/endpoints/{endpoint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_endpoint(endpoint_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_endpoint = crud.delete_endpoint(db, endpoint_id=endpoint_id)
    if db_endpoint is None:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return None

@app.get("/endpoints/{endpoint_id}/logs", response_model=List[schemas.PingLog])
def read_ping_logs(endpoint_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_endpoint = crud.get_endpoint(db, endpoint_id=endpoint_id)
    if db_endpoint is None:
        raise HTTPException(status_code=404, detail="Endpoint not found")
    return crud.get_ping_logs(db, endpoint_id=endpoint_id, skip=skip, limit=limit)