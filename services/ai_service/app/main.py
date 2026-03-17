import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.mongodb import close_db, connect_db
from app.clients.qdrant import close_qdrant_client, get_qdrant_client
from app.logging_config import setup_logging
from app.observability import init_tracing
from app.routers.analyze import router as analyze_router
from app.routers.chat import router as chat_router

setup_logging("ai-service")
logger = logging.getLogger("ai-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage AI service startup and shutdown lifecycle."""
    logger.info("Starting AI service")
    init_tracing()
    await connect_db()
    get_qdrant_client()
    logger.info("All clients initialized")
    yield
    close_qdrant_client()
    await close_db()
    logger.info("AI service shut down")


app = FastAPI(title="Course Finder AI Service", lifespan=lifespan)

app.include_router(chat_router)
app.include_router(analyze_router)


@app.get("/health")
async def health():
    """Return service health status with dependency checks."""
    checks = {}
    overall = "ok"

    # Check MongoDB
    try:
        from app.clients.mongodb import get_db

        db = get_db()
        await db.command("ping")
        checks["mongodb"] = "ok"
    except Exception as e:
        checks["mongodb"] = f"degraded: {e}"
        overall = "degraded"

    # Check Qdrant
    try:
        qdrant = get_qdrant_client()
        collections = qdrant.get_collections()
        checks["qdrant"] = f"ok ({len(collections.collections)} collections)"
    except Exception as e:
        checks["qdrant"] = f"degraded: {e}"
        overall = "degraded"

    return {"status": overall, "service": "ai-service", "checks": checks}
