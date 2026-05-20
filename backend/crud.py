from sqlalchemy.orm import Session
import models, schemas

def get_user_by_username(db: Session, username: str):
    """Retrieve a user by their username."""
    return db.query(models.User).filter(models.User.username == username).first()

def get_endpoint(db: Session, endpoint_id: int):
    """Retrieve a single endpoint by its ID."""
    return db.query(models.Endpoint).filter(models.Endpoint.id == endpoint_id).first()

def get_endpoints(db: Session, skip: int = 0, limit: int = 100):
    """Retrieve a paginated list of endpoints."""
    return db.query(models.Endpoint).offset(skip).limit(limit).all()

def create_endpoint(db: Session, endpoint: schemas.EndpointCreate):
    """Create a new endpoint record in the database."""
    db_endpoint = models.Endpoint(
        name=endpoint.name,
        url=str(endpoint.url), # Convert HttpUrl to string for DB storage
        expected_status=endpoint.expected_status,
        check_interval_minutes=endpoint.check_interval_minutes
    )
    db.add(db_endpoint)
    db.commit()
    db.refresh(db_endpoint)
    return db_endpoint

def update_endpoint(db: Session, endpoint_id: int, endpoint: schemas.EndpointCreate):
    """Update an existing endpoint."""
    db_endpoint = get_endpoint(db, endpoint_id)
    if db_endpoint:
        db_endpoint.name = endpoint.name
        db_endpoint.url = str(endpoint.url)
        db_endpoint.expected_status = endpoint.expected_status
        db_endpoint.check_interval_minutes = endpoint.check_interval_minutes
        db.commit()
        db.refresh(db_endpoint)
    return db_endpoint

def delete_endpoint(db: Session, endpoint_id: int):
    """Delete an endpoint by its ID."""
    db_endpoint = get_endpoint(db, endpoint_id)
    if db_endpoint:
        db.delete(db_endpoint)
        db.commit()
    return db_endpoint

def get_ping_logs(db: Session, endpoint_id: int, skip: int = 0, limit: int = 50):
    """Retrieve a paginated history of ping logs for a specific endpoint, ordered by newest first."""
    return (
        db.query(models.PingLog)
        .filter(models.PingLog.endpoint_id == endpoint_id)
        .order_by(models.PingLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )