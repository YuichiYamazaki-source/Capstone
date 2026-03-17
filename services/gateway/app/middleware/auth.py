import logging

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

_bearer_scheme = HTTPBearer(auto_error=False)
logger = logging.getLogger("gateway.auth")


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        logger.warning("JWT decode failed: invalid or expired token")
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """Extract and validate user ID from a required Bearer token.

    Args:
        credentials: HTTP Bearer credentials injected by FastAPI.

    Returns:
        The authenticated user ID from the JWT 'sub' claim.

    Raises:
        HTTPException: If credentials are missing or the token is invalid.
    """
    if not credentials:
        logger.warning("Authentication required but no credentials provided")
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = _decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        logger.warning("JWT payload missing 'sub' claim")
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return user_id


async def optional_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str | None:
    """Extract user ID from a Bearer token if present, without requiring auth.

    Args:
        credentials: HTTP Bearer credentials injected by FastAPI.

    Returns:
        The user ID if a valid token is provided, otherwise None.
    """
    if not credentials:
        return None
    try:
        payload = _decode_token(credentials.credentials)
        return payload.get("sub")
    except HTTPException:
        return None
