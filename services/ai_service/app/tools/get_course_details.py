"""Retrieve full details of a specific course."""

import logging

from agents import function_tool

from app.agent.context import add_tool_call
from app.clients.mongodb import get_db

logger = logging.getLogger("ai-service.tools.get_course_details")


@function_tool
async def get_course_details(course_title: str) -> str:
    """Get full details of a course by title.

    Use when you need complete information about a specific course
    (description, instructor, schedule, URL).

    Args:
        course_title: Exact or partial title of the course.
    """
    add_tool_call("get_course_details")
    db = get_db()

    doc = await db.courses.find_one(
        {"title": {"$regex": course_title, "$options": "i"}},
    )

    if not doc:
        return f"[ERROR] get_course_details: No course found matching '{course_title}'."

    details = [
        f"Title: {doc.get('title', 'N/A')}",
        f"Description: {doc.get('description', 'N/A')}",
        f"Organization: {doc.get('organization', 'N/A')}",
        f"Instructor: {doc.get('instructor', 'N/A')}",
        f"Level: {doc.get('level', 'N/A')}",
        f"Rating: {doc.get('rating', 'N/A')}",
        f"Reviews: {doc.get('num_reviews', 'N/A')}",
        f"Enrolled: {doc.get('enrolled', 'N/A')}",
        f"Skills: {', '.join(doc.get('skills', []))}",
        f"Modules: {doc.get('modules', 'N/A')}",
        f"Schedule: {doc.get('schedule', 'N/A')}",
        f"URL: {doc.get('url', 'N/A')}",
    ]

    logger.info(
        "Course details retrieved",
        extra={"title": doc.get("title")},
    )

    return "\n".join(details)
