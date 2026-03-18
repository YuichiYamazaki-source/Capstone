import logging
import re

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings
from app.models.course import Course, CourseListResponse, FilterOptions

logger = logging.getLogger("course-service.db")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """Connect to MongoDB and create indexes on the courses collection."""
    global _client, _db
    _client = AsyncIOMotorClient(settings.mongo_uri)
    _db = _client[settings.mongo_db]
    await _db.courses.create_index("title")
    await _db.courses.create_index("level")
    await _db.courses.create_index("organization")
    await _db.courses.create_index("skills")
    count = await _db.courses.count_documents({})
    logger.info(
        "Database ready", extra={"collection": "courses", "document_count": count}
    )


async def close_db() -> None:
    """Close the MongoDB client connection."""
    global _client
    if _client:
        _client.close()
        logger.info("Database connection closed")


def _get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not connected")
    return _db


def _doc_to_course(doc: dict) -> Course:
    return Course(
        id=str(doc["_id"]),
        title=doc["title"],
        description=doc.get("description", ""),
        organization=doc.get("organization", ""),
        instructor=doc.get("instructor", ""),
        level=doc.get("level", "Unknown"),
        rating=doc.get("rating"),
        num_reviews=doc.get("num_reviews"),
        enrolled=doc.get("enrolled"),
        skills=doc.get("skills", []),
        modules=doc.get("modules", ""),
        schedule=doc.get("schedule"),
        url=doc.get("url", ""),
        satisfaction_rate=doc.get("satisfaction_rate"),
    )


async def get_all_courses(
    level: str | None = None,
    organization: str | None = None,
    min_rating: float | None = None,
    skills: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
) -> CourseListResponse:
    """Retrieve courses with optional filters and pagination.

    Args:
        level: Filter by course level (case-insensitive).
        organization: Filter by organization name (case-insensitive).
        min_rating: Filter by minimum rating threshold.
        skills: Filter by skill tags.
        limit: Maximum number of courses to return.
        offset: Number of courses to skip.

    Returns:
        Paginated response containing matching courses.
    """
    db = _get_db()
    query: dict = {}

    if level:
        query["level"] = re.compile(f"^{re.escape(level)}$", re.IGNORECASE)

    if organization:
        query["organization"] = re.compile(re.escape(organization), re.IGNORECASE)

    if min_rating is not None:
        query["rating"] = {"$gte": min_rating}

    if skills:
        skills_lower = [s.lower() for s in skills]
        query["skills_lower"] = {"$in": skills_lower}

    total = await db.courses.count_documents(query)
    cursor = db.courses.find(query).skip(offset).limit(limit)
    docs = await cursor.to_list(length=limit)

    courses = [_doc_to_course(d) for d in docs]
    return CourseListResponse(courses=courses, total=total, limit=limit, offset=offset)


async def search_courses(
    query: str, limit: int = 20, offset: int = 0
) -> CourseListResponse:
    """Search courses by text across title, description, and skills.

    Args:
        query: Text to search for (case-insensitive regex).
        limit: Maximum number of courses to return.
        offset: Number of courses to skip.

    Returns:
        Paginated response containing matching courses.
    """
    db = _get_db()
    regex = re.compile(re.escape(query), re.IGNORECASE)
    mongo_query = {
        "$or": [
            {"title": regex},
            {"description": regex},
            {"skills": regex},
        ]
    }

    total = await db.courses.count_documents(mongo_query)
    cursor = db.courses.find(mongo_query).skip(offset).limit(limit)
    docs = await cursor.to_list(length=limit)

    courses = [_doc_to_course(d) for d in docs]
    return CourseListResponse(courses=courses, total=total, limit=limit, offset=offset)


async def get_course_by_id(course_id: str) -> Course | None:
    """Retrieve a single course by its MongoDB ObjectId.

    Args:
        course_id: The string representation of the ObjectId.

    Returns:
        The matching course, or None if not found.
    """
    db = _get_db()
    from bson import ObjectId

    try:
        doc = await db.courses.find_one({"_id": ObjectId(course_id)})
    except Exception:
        return None

    if not doc:
        return None
    return _doc_to_course(doc)


async def search_skills(
    query: str = "", limit: int = 20
) -> list[dict]:
    """Search skills by prefix, ranked by frequency across courses.

    Args:
        query: Partial skill name to match (case-insensitive).
        limit: Maximum number of skills to return.

    Returns:
        List of dicts with skill name and course count, sorted by frequency.
    """
    db = _get_db()
    pipeline: list[dict] = [
        {"$unwind": "$skills"},
    ]
    if query:
        pipeline.append(
            {"$match": {"skills": re.compile(re.escape(query), re.IGNORECASE)}}
        )
    pipeline.extend([
        {"$group": {"_id": "$skills", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"_id": 0, "skill": "$_id", "count": 1}},
    ])
    return await db.courses.aggregate(pipeline).to_list(length=limit)


async def get_filter_options() -> FilterOptions:
    """Retrieve distinct filter values for levels, organizations, and skills."""
    db = _get_db()
    levels = await db.courses.distinct("level")
    organizations = await db.courses.distinct("organization")
    skills: list[str] = await db.courses.distinct("skills")

    return FilterOptions(
        levels=sorted([lv for lv in levels if lv]),
        organizations=sorted([o for o in organizations if o]),
        skills=sorted([s for s in skills if s]),
    )
