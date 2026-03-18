import logging

import httpx
from fastapi import APIRouter, Request, Response

from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["ai"])
logger = logging.getLogger("gateway.proxy.ai")

# Shared httpx client with connection pooling (zero per-request TCP overhead)
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    """Return the shared httpx client, creating it on first call."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10,
            ),
        )
    return _http_client


async def close_http_client() -> None:
    """Close the shared httpx client on shutdown."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


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
    client = _get_http_client()
    try:
        resp = await client.post(
            url,
            content=body,
            headers={"content-type": "application/json"},
            timeout=timeout,
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


@router.get("/analyze/results/{user_id}")
async def get_saved_results(user_id: str) -> Response:
    """Proxy saved analysis results from the AI service."""
    url = f"{settings.ai_service_url}/analyze/results/{user_id}"
    client = _get_http_client()
    try:
        resp = await client.get(url, timeout=10.0)
    except httpx.ConnectError:
        logger.error("AI service unreachable", extra={"target_url": url})
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
