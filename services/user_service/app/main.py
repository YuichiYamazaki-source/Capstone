import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.logging_config import setup_logging
from app.routers.auth import router as auth_router
from app.routers.profile import router as profile_router
from app.services.user_service import close_db, connect_db

setup_logging("user-service")
logger = logging.getLogger("user-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage user service startup and shutdown lifecycle.

    Args:
        app: The FastAPI application instance.
    """
    logger.info("Starting user service")
    await connect_db()
    logger.info("MongoDB connected")
    yield
    await close_db()
    logger.info("MongoDB disconnected, shutting down")


app = FastAPI(title="User Service", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(profile_router)


@app.get("/health")
def health():
    """Return user service health status."""
    return {"status": "ok", "service": "user-service"}
