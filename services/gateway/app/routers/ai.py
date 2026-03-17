import logging

import httpx
from fastapi import APIRouter, Request, Response

from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["ai"])
logger = logging.getLogger("gateway.proxy.ai")


async def _proxy_to_ai(request: Request, path: str, timeout: float = 120.0) -> Response:
    """Forward a request to the AI service.

    Args:
        request: Incoming FastAPI request to forward.
        path: AI service endpoint path (e.g. "/chat").
        timeout: Request timeout in seconds.

    Returns:
        Proxied response from the AI service.
    """
    url = f"{settings.ai_service_url}{path}"
    body = await request.body()
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(
                url,
                content=body,
                headers={"content-type": "application/json"},
            )
        except httpx.ConnectError:
            logger.error(
                "AI service unreachable",
                extra={"target_url": url},
            )
            return Response(
                content='{"detail":"AI service unavailable"}',
                status_code=503,
                media_type="application/json",
            )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type="application/json",
    )


@router.post("/chat")
async def chat(request: Request) -> Response:
    """Proxy chat requests to the AI service."""
    return await _proxy_to_ai(request, "/chat", timeout=180.0)


@router.post("/analyze")
async def analyze(request: Request) -> Response:
    """Proxy analyze requests to the AI service."""
    return await _proxy_to_ai(request, "/analyze", timeout=180.0)


@router.post("/analyze/skill-gap")
async def analyze_skill_gap(request: Request) -> Response:
    """Proxy skill gap analysis to the AI service."""
    return await _proxy_to_ai(request, "/analyze/skill-gap", timeout=120.0)


@router.post("/analyze/career")
async def analyze_career(request: Request) -> Response:
    """Proxy career analysis to the AI service."""
    return await _proxy_to_ai(request, "/analyze/career", timeout=120.0)


@router.post("/analyze/learning-path")
async def analyze_learning_path(request: Request) -> Response:
    """Proxy learning path analysis to the AI service."""
    return await _proxy_to_ai(request, "/analyze/learning-path", timeout=120.0)
