"""
Auth router — register, login, me
"""
from fastapi import APIRouter, HTTPException, status, Depends
from passlib.context import CryptContext
from datetime import datetime
from bson import ObjectId

from database import get_db
from middleware.auth import create_access_token, get_current_user
from models.user import UserCreate, UserLogin, UserOut, TokenResponse

router = APIRouter()
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _serialize_user(doc: dict) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        created_at=doc["created_at"],
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: UserCreate):
    db = get_db()

    if await db.users.find_one({"email": payload.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    now = datetime.utcnow()
    user_doc = {
        "name": payload.name,
        "email": payload.email,
        "password_hash": pwd_ctx.hash(payload.password),
        "created_at": now,
        "updated_at": now,
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    token = create_access_token(str(result.inserted_id))
    return TokenResponse(access_token=token, user=_serialize_user(user_doc))


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    db = get_db()
    user = await db.users.find_one({"email": payload.email})

    if not user or not pwd_ctx.verify(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(str(user["_id"]))
    return TokenResponse(access_token=token, user=_serialize_user(user))


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    return _serialize_user(current_user)
