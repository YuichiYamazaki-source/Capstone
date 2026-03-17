import logging

import httpx
from fastapi import APIRouter, Request, Response

from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["ai"])
logger = logging.getLogger("gateway.proxy.ai")


@router.post("/chat")
async def chat(request: Request) -> Response:
    """Proxy chat requests to the AI service.

    Args:
        request: Incoming FastAPI request to forward.

    Returns:
        Proxied response from the AI service.
    """
    url = f"{settings.ai_service_url}/chat"
    body = await request.body()
    async with httpx.AsyncClient(timeout=120.0) as client:
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
