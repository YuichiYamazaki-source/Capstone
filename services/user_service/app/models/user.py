from datetime import datetime

from pydantic import BaseModel, EmailStr


class SkillEntry(BaseModel):
    """A skill with self-assessed proficiency level."""

    name: str
    level: str = "Beginner"


class UserProfile(BaseModel):
    """User learning profile with skills and preferences."""

    skills: list[SkillEntry] = []
    motivation: str | None = None
    learning_scope: str | None = None
    learning_style: str | None = None
    interest_areas: list[str] = []


class UserCreate(BaseModel):
    """Request body for user registration."""

    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public user data returned in API responses."""

    id: str
    email: str
    name: str
    profile: UserProfile
    created_at: datetime


class ProfileUpdate(BaseModel):
    """Request body for partial profile updates."""

    skills: list[SkillEntry] | None = None
    motivation: str | None = None
    learning_scope: str | None = None
    learning_style: str | None = None
    interest_areas: list[str] | None = None


class TokenResponse(BaseModel):
    """JWT token with associated user data."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
