from pydantic import BaseModel


class Course(BaseModel):
    """Representation of a single course."""

    id: str
    title: str
    description: str
    organization: str
    instructor: str
    level: str
    rating: float | None = None
    num_reviews: int | None = None
    enrolled: str | None = None
    skills: list[str] = []
    modules: str
    schedule: str | None = None
    url: str
    satisfaction_rate: str | None = None


class CourseListResponse(BaseModel):
    """Paginated list of courses with total count."""

    courses: list[Course]
    total: int
    limit: int
    offset: int


class FilterOptions(BaseModel):
    """Available filter options for course search."""

    levels: list[str]
    organizations: list[str]
    skills: list[str]
