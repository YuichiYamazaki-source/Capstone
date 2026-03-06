"""
routes.py
Auth Service endpoints: /auth/register, /auth/login
"""

from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext

from src.shared.database import get_db
from src.shared.jwt import create_token
from src.shared.logging import setup_logger
from .models import UserCreate, UserLogin, Token

logger = setup_logger("auth")

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserCreate):
    db = get_db()
    if db.users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    doc = {
        "email": user.email,
        "name": user.name,
        "hashed_password": pwd_context.hash(user.password),
    }
    result = db.users.insert_one(doc)
    logger.info("user_registered email=%s user_id=%s", user.email, result.inserted_id)
    return {"user_id": str(result.inserted_id)}


@router.post("/login", response_model=Token)
def login(credentials: UserLogin):
    db = get_db()
    user = db.users.find_one({"email": credentials.email})
    if not user or not pwd_context.verify(credentials.password, user["hashed_password"]):
        logger.warning("login_failed email=%s", credentials.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(str(user["_id"]))
    logger.info("login_success email=%s", credentials.email)
    return Token(access_token=token)
