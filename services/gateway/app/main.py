import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import setup_logging
from app.routers.ai import router as ai_router
from app.routers.courses import router as courses_router
from app.routers.users import router as users_router

setup_logging("gateway")
logger = logging.getLogger("gateway")

app = FastAPI(title="Course Finder Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log every request with method, path, status, and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    # Skip health check noise
    if request.url.path == "/health":
        return response

    logger.info(
        "Request handled",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "client": request.client.host if request.client else None,
        },
    )
    return response


app.include_router(courses_router)
app.include_router(users_router)
app.include_router(ai_router)


@app.get("/health")
def health():
    """Return service health status."""
    return {"status": "ok", "service": "gateway"}
