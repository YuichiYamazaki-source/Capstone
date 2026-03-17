import logging

import httpx
from fastapi import APIRouter, Depends, Request, Response

from app.config import settings
from app.middleware.auth import require_auth

router = APIRouter(prefix="/api/v1", tags=["users"])
logger = logging.getLogger("gateway.proxy.users")


@router.post("/auth/register")
async def register(request: Request):
    """Proxy user registration to the user service.

    Args:
        request: Incoming FastAPI request with registration payload.
    """
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.user_service_url}/auth/register",
                content=body,
                headers={"content-type": "application/json"},
            )
        except httpx.ConnectError:
            logger.error("User service unreachable for registration")
            return Response(
                content='{"detail":"User service unavailable"}',
                status_code=503,
                media_type="application/json",
            )
    if resp.status_code == 200:
        logger.info("User registered successfully")
    else:
        logger.warning(
            "Registration failed",
            extra={"status_code": resp.status_code},
        )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type="application/json",
    )


@router.post("/auth/login")
async def login(request: Request):
    """Proxy user login to the user service.

    Args:
        request: Incoming FastAPI request with login credentials.
    """
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.user_service_url}/auth/login",
                content=body,
                headers={"content-type": "application/json"},
            )
        except httpx.ConnectError:
            logger.error("User service unreachable for login")
            return Response(
                content='{"detail":"User service unavailable"}',
                status_code=503,
                media_type="application/json",
            )
    if resp.status_code == 200:
        logger.info("User login successful")
    else:
        logger.warning(
            "Login failed",
            extra={"status_code": resp.status_code},
        )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type="application/json",
    )


@router.get("/users/profile")
async def get_profile(user_id: str = Depends(require_auth)):
    """Proxy authenticated user profile retrieval to the user service.

    Args:
        user_id: Authenticated user ID extracted from the JWT.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.user_service_url}/users/profile",
                headers={"x-user-id": user_id},
            )
        except httpx.ConnectError:
            logger.error("User service unreachable for profile fetch")
            return Response(
                content='{"detail":"User service unavailable"}',
                status_code=503,
                media_type="application/json",
            )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type="application/json",
    )


@router.put("/users/profile")
async def update_profile(request: Request, user_id: str = Depends(require_auth)):
    """Proxy authenticated user profile update to the user service.

    Args:
        request: Incoming FastAPI request with profile update payload.
        user_id: Authenticated user ID extracted from the JWT.
    """
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.put(
                f"{settings.user_service_url}/users/profile",
                content=body,
                headers={
                    "content-type": "application/json",
                    "x-user-id": user_id,
                },
            )
        except httpx.ConnectError:
            logger.error("User service unreachable for profile update")
            return Response(
                content='{"detail":"User service unavailable"}',
                status_code=503,
                media_type="application/json",
            )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type="application/json",
    )
