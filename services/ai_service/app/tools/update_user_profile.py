"""Update user profile fields in MongoDB."""

import logging

from agents import function_tool
from bson import ObjectId

from app.clients.mongodb import get_db

logger = logging.getLogger("ai-service.tools.update_user_profile")


@function_tool
async def update_user_profile(
    user_id: str,
    skills: list[str] | None = None,
    motivation: str | None = None,
    interest_areas: list[str] | None = None,
) -> str:
    """Update the user's profile with new information learned from conversation.

    Only update fields that the user has explicitly mentioned.

    Args:
        user_id: The user's ID.
        skills: Updated list of skills (replaces existing).
        motivation: Updated motivation/goal statement.
        interest_areas: Updated list of interest areas (replaces existing).
    """
    db = get_db()

    update_fields: dict = {}
    if skills is not None:
        update_fields["profile.skills"] = skills
    if motivation is not None:
        update_fields["profile.motivation"] = motivation
    if interest_areas is not None:
        update_fields["profile.interest_areas"] = interest_areas

    if not update_fields:
        return "No fields to update."

    try:
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_fields},
        )
    except Exception:
        return f"Invalid user ID: {user_id}"

    if result.matched_count == 0:
        return f"No user found with ID '{user_id}'."

    updated = list(update_fields.keys())
    logger.info(
        "User profile updated",
        extra={"user_id": user_id, "updated_fields": updated},
    )

    return f"Profile updated: {', '.join(f.replace('profile.', '') for f in updated)}"
