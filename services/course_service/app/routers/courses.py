from fastapi import APIRouter, HTTPException, Query

from app.models.course import Course, CourseListResponse, FilterOptions
from app.services.course_service import (
    get_all_courses,
    get_course_by_id,
    get_filter_options,
    search_courses,
)

router = APIRouter()


@router.get("/courses", response_model=CourseListResponse)
async def list_courses(
    level: str | None = None,
    organization: str | None = None,
    min_rating: float | None = None,
    skills: list[str] | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List courses with optional filtering and pagination.

    Args:
        level: Filter by course level.
        organization: Filter by organization name.
        min_rating: Filter by minimum rating.
        skills: Filter by skill tags.
        limit: Maximum number of courses to return.
        offset: Number of courses to skip.

    Returns:
        Paginated course list matching the filters.
    """
    return await get_all_courses(
        level=level,
        organization=organization,
        min_rating=min_rating,
        skills=skills,
        limit=limit,
        offset=offset,
    )


@router.get("/courses/search", response_model=CourseListResponse)
async def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Search courses by text query with pagination.

    Args:
        q: Search query string.
        limit: Maximum number of courses to return.
        offset: Number of courses to skip.

    Returns:
        Paginated course list matching the query.
    """
    return await search_courses(query=q, limit=limit, offset=offset)


@router.get("/courses/{course_id}", response_model=Course)
async def get_course(course_id: str):
    """Retrieve a single course by its ID.

    Args:
        course_id: The MongoDB ObjectId of the course.

    Returns:
        The matching course.

    Raises:
        HTTPException: If the course is not found.
    """
    course = await get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/filters/options", response_model=FilterOptions)
async def filter_options():
    """Return available filter options for levels, organizations, and skills."""
    return await get_filter_options()
