import asyncio
import httpx
import os
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
import logging

from database import SessionLocal
import models, crud

# Setup basic logging for the scheduler
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Telegram configurations from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

async def send_telegram_alert(endpoint_name: str, url: str):
    """Sends a Telegram message via bot API when an endpoint goes down."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not set. Skipping alert.")
        return
    
    message = f"🚨 *ALERT*: Endpoint Down!\n\n*Name*: {endpoint_name}\n*URL*: {url}\n\nThe endpoint is currently failing expected health checks."
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(api_url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            })
            logger.info(f"Telegram alert sent for {endpoint_name}")
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")

async def ping_url(client: httpx.AsyncClient, endpoint: models.Endpoint, db: Session):
    """Pings a single endpoint and logs the result."""
    start_time = datetime.now(timezone.utc)
    status_code = None
    is_success = False
    response_time_ms = None
    
    try:
        # Send GET request with a timeout
        response = await client.get(endpoint.url, timeout=10.0)
        status_code = response.status_code
        response_time_ms = response.elapsed.total_seconds() * 1000
        is_success = (status_code == endpoint.expected_status)
    except httpx.RequestError as exc:
        response_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        logger.warning(f"Failed to ping {endpoint.url}: {exc}")
    
    # Check the LAST log to determine if there's a state change (Up -> Down)
    last_log = db.query(models.PingLog).filter(
        models.PingLog.endpoint_id == endpoint.id
    ).order_by(models.PingLog.timestamp.desc()).first()
    
    # Create PingLog entry
    ping_log = models.PingLog(
        endpoint_id=endpoint.id,
        status_code=status_code,
        response_time_ms=response_time_ms,
        is_success=is_success,
        timestamp=start_time
    )
    
    db.add(ping_log)
    db.commit()

    # Trigger Telegram Alert if it changed from Success (True) to Failed (False)
    if last_log and last_log.is_success and not is_success:
        await send_telegram_alert(endpoint.name, endpoint.url)

async def check_all_endpoints():
    """Background job to check all registered endpoints."""
    db: Session = SessionLocal()
    try:
        endpoints = crud.get_endpoints(db, skip=0, limit=10000)
        if not endpoints:
            return
        
        async with httpx.AsyncClient() as client:
            tasks = [ping_url(client, endpoint, db) for endpoint in endpoints]
            await asyncio.gather(*tasks)
            
    except Exception as e:
        logger.error(f"Error running check_all_endpoints: {e}")
    finally:
        db.close()

scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.add_job(check_all_endpoints, 'interval', minutes=1, id='check_endpoints_job', replace_existing=True)
    scheduler.start()
    logger.info("Background scheduler started.")
    
def stop_scheduler():
    scheduler.shutdown()
    logger.info("Background scheduler stopped.")