from fastapi import APIRouter, HTTPException

from app.models.user import TokenResponse, UserCreate, UserLogin
from app.services.user_service import login_user, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate):
    """Register a new user and return a JWT token.

    Args:
        data: User registration payload with email, password, and name.

    Returns:
        JWT token and user data.

    Raises:
        HTTPException: If the email is already registered.
    """
    try:
        return await register_user(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    """Authenticate a user and return a JWT token.

    Args:
        data: Login payload with email and password.

    Returns:
        JWT token and user data.

    Raises:
        HTTPException: If credentials are invalid.
    """
    try:
        return await login_user(data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
