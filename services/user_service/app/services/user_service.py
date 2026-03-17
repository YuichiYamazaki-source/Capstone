import logging
from datetime import UTC, datetime, timedelta

from jose import jwt
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from passlib.context import CryptContext

from app.config import settings
from app.models.user import (
    ProfileUpdate,
    TokenResponse,
    UserCreate,
    UserProfile,
    UserResponse,
)

logger = logging.getLogger("user-service.db")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    """Connect to MongoDB and create indexes on the users collection."""
    global _client, _db
    _client = AsyncIOMotorClient(settings.mongo_uri)
    _db = _client[settings.mongo_db]
    await _db.users.create_index("email", unique=True)
    count = await _db.users.count_documents({})
    logger.info(
        "Database ready", extra={"collection": "users", "document_count": count}
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


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(hours=settings.jwt_expire_hours)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def _user_response(doc: dict) -> UserResponse:
    return UserResponse(
        id=str(doc["_id"]),
        email=doc["email"],
        name=doc["name"],
        profile=UserProfile(**doc.get("profile", {})),
        created_at=doc["created_at"],
    )


async def register_user(data: UserCreate) -> TokenResponse:
    """Register a new user and return a JWT token.

    Args:
        data: Registration data with email, password, and name.

    Returns:
        Token response with JWT and user data.

    Raises:
        ValueError: If the email is already registered.
    """
    db = _get_db()

    existing = await db.users.find_one({"email": data.email})
    if existing:
        logger.warning(
            "Registration rejected: email already exists", extra={"email": data.email}
        )
        raise ValueError("Email already registered")

    now = datetime.now(UTC)
    doc = {
        "email": data.email,
        "hashed_password": _hash_password(data.password),
        "name": data.name,
        "profile": UserProfile().model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id

    token = _create_token(str(result.inserted_id))
    logger.info("User registered", extra={"user_id": str(result.inserted_id)})
    return TokenResponse(access_token=token, user=_user_response(doc))


async def login_user(email: str, password: str) -> TokenResponse:
    """Authenticate a user by email and password.

    Args:
        email: User's email address.
        password: Plain-text password to verify.

    Returns:
        Token response with JWT and user data.

    Raises:
        ValueError: If credentials are invalid.
    """
    db = _get_db()
    doc = await db.users.find_one({"email": email})
    if not doc or not _verify_password(password, doc["hashed_password"]):
        logger.warning("Login failed: invalid credentials", extra={"email": email})
        raise ValueError("Invalid email or password")

    token = _create_token(str(doc["_id"]))
    logger.info("User logged in", extra={"user_id": str(doc["_id"])})
    return TokenResponse(access_token=token, user=_user_response(doc))


async def get_user_profile(user_id: str) -> UserResponse:
    """Retrieve a user's profile by ID.

    Args:
        user_id: The string representation of the user's ObjectId.

    Returns:
        The user's profile data.

    Raises:
        ValueError: If the user is not found.
    """
    db = _get_db()
    from bson import ObjectId

    doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not doc:
        raise ValueError("User not found")
    return _user_response(doc)


async def update_user_profile(user_id: str, data: ProfileUpdate) -> UserResponse:
    """Update a user's profile with the provided fields.

    Args:
        user_id: The string representation of the user's ObjectId.
        data: Partial profile fields to update.

    Returns:
        The updated user profile.

    Raises:
        ValueError: If no fields are provided or the user is not found.
    """
    db = _get_db()
    from bson import ObjectId

    update_fields = {}
    for field, value in data.model_dump(exclude_none=True).items():
        update_fields[f"profile.{field}"] = value

    if not update_fields:
        raise ValueError("No fields to update")

    update_fields["updated_at"] = datetime.now(UTC)

    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_fields},
    )

    doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not doc:
        raise ValueError("User not found")
    return _user_response(doc)
