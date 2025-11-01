"""
Main FastAPI application
Contract Intelligence Parser API
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routes import contracts

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    Handles startup and shutdown events
    """
    # Startup
    logger.info("Starting Contract Intelligence API...")
    try:
        connect_to_mongo()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Contract Intelligence API...")
    close_mongo_connection()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Automated contract parsing and intelligence system for accounts receivable",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    contracts.router,
    prefix="/contracts",
    tags=["contracts"]
)


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint - API health check
    """
    return {
        "status": "online",
        "api": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Comprehensive health check
    """
    try:
        from app.database import get_database
        from redis import Redis
        
        # Check MongoDB
        db_status = "healthy"
        try:
            db = get_database()
            db.command('ping')
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Check Redis
        redis_status = "healthy"
        try:
            redis_client = Redis.from_url(settings.redis_url)
            redis_client.ping()
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
        
        overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"
        
        return {
            "status": overall_status,
            "database": db_status,
            "redis": redis_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )