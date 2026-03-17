from fastapi import APIRouter, Header, HTTPException

from app.models.user import ProfileUpdate, UserResponse
from app.services.user_service import get_user_profile, update_user_profile

router = APIRouter(prefix="/users", tags=["profile"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(x_user_id: str = Header(...)):
    """Retrieve the authenticated user's profile.

    Args:
        x_user_id: User ID from the gateway-injected header.

    Returns:
        The user's profile data.

    Raises:
        HTTPException: If the user is not found.
    """
    try:
        return await get_user_profile(x_user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: ProfileUpdate,
    x_user_id: str = Header(...),
):
    """Update the authenticated user's profile fields.

    Args:
        data: Partial profile update payload.
        x_user_id: User ID from the gateway-injected header.

    Returns:
        The updated user profile.

    Raises:
        HTTPException: If the update fails or user is not found.
    """
    try:
        return await update_user_profile(x_user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
