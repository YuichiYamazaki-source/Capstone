"""Retrieve user profile from MongoDB."""

import logging

from agents import function_tool
from bson import ObjectId

from app.clients.mongodb import get_db

logger = logging.getLogger("ai-service.tools.get_user_profile")


@function_tool
async def get_user_profile(user_id: str) -> str:
    """Get the user's profile including skills, goals, and interests.

    Use to personalize recommendations based on the user's background.

    Args:
        user_id: The user's ID.
    """
    db = get_db()

    try:
        doc = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return f"[ERROR] get_user_profile: Invalid user ID '{user_id}'."

    if not doc:
        return f"[ERROR] get_user_profile: No user found with ID '{user_id}'."

    profile = doc.get("profile", {})
    info = [
        f"Name: {doc.get('name', 'N/A')}",
        f"Skills: {', '.join(profile.get('skills', [])) or 'None listed'}",
        f"Motivation: {profile.get('motivation') or 'Not specified'}",
        f"Learning Scope: {profile.get('learning_scope') or 'Not specified'}",
        f"Learning Style: {profile.get('learning_style') or 'Not specified'}",
        f"Interest Areas: {', '.join(profile.get('interest_areas', [])) or 'None listed'}",
    ]

    logger.info("User profile retrieved", extra={"user_id": user_id})

    return "\n".join(info)
