import logging

import httpx
from fastapi import APIRouter, Request, Response

from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["courses"])
logger = logging.getLogger("gateway.proxy.courses")


async def _proxy_get(path: str, request: Request) -> Response:
    url = f"{settings.course_service_url}{path}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=dict(request.query_params))
        except httpx.ConnectError:
            logger.error(
                "Course service unreachable",
                extra={"target_url": url},
            )
            return Response(
                content='{"detail":"Course service unavailable"}',
                status_code=503,
                media_type="application/json",
            )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type="application/json",
    )


@router.get("/courses")
async def list_courses(request: Request):
    """Proxy paginated course listing to the course service."""
    return await _proxy_get("/courses", request)


@router.get("/courses/search")
async def search_courses(request: Request):
    """Proxy course search queries to the course service."""
    return await _proxy_get("/courses/search", request)


@router.get("/filters/options")
async def filter_options(request: Request):
    """Proxy filter options request to the course service."""
    return await _proxy_get("/filters/options", request)


@router.get("/courses/{course_id}")
async def get_course(course_id: str, request: Request):
    """Proxy single course retrieval to the course service.

    Args:
        course_id: The course identifier to look up.
        request: Incoming FastAPI request.
    """
    return await _proxy_get(f"/courses/{course_id}", request)
