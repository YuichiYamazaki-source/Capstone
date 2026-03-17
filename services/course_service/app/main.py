import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.logging_config import setup_logging
from app.routers.courses import router as courses_router
from app.services.course_service import close_db, connect_db

setup_logging("course-service")
logger = logging.getLogger("course-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage course service startup and shutdown lifecycle.

    Args:
        app: The FastAPI application instance.
    """
    logger.info("Starting course service")
    await connect_db()
    logger.info("MongoDB connected")
    yield
    await close_db()
    logger.info("MongoDB disconnected, shutting down")


app = FastAPI(title="Course Service", lifespan=lifespan)
app.include_router(courses_router)


@app.get("/health")
def health():
    """Return course service health status."""
    return {"status": "ok", "service": "course-service"}
