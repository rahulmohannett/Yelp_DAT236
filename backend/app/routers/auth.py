from bson import ObjectId
"""
Authentication router for user registration and login.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.schemas import UserCreate, UserLogin, Token, UserResponse
from app.services.auth import hash_password, verify_password, create_access_token
from datetime import datetime, timedelta
from app.models import to_str_id

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db=Depends(get_db)):
    """Register a new user."""
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    new_user = {
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "role": user_data.role,
        "city": user_data.city,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    result = await db.users.insert_one(new_user)
    new_user["_id"] = result.inserted_id

    access_token = create_access_token(data={"sub": str(new_user["_id"])})
    return Token(access_token=access_token, user=UserResponse.model_validate(to_str_id(new_user)))


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db=Depends(get_db)):
    """Login a user."""
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    # Save session with 7 day expiry
    await db.sessions.insert_one({
        "user_id": user["_id"],
        "expires_at": datetime.utcnow() + timedelta(days=7),
        "created_at": datetime.utcnow()
    })

    access_token = create_access_token(data={"sub": str(user["_id"])})
    return Token(access_token=access_token, user=UserResponse.model_validate(to_str_id(user)))
