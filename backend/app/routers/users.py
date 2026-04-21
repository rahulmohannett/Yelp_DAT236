"""
User management router with profile picture upload.
"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.database import get_db
from app.schemas import UserResponse, UserUpdate, UserPreferencesCreate, UserPreferencesResponse
from app.services.auth import get_current_user
from app.config import settings
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/users", tags=["Users"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user=Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Update current user profile."""
    update_fields = {k: v for k, v in user_data.model_dump(exclude_unset=True).items()}
    update_fields["updated_at"] = datetime.utcnow()

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_fields}
    )
    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    return UserResponse.model_validate(updated_user)


@router.post("/me/profile-picture", response_model=UserResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Upload a profile picture."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be JPEG, PNG, GIF, or WEBP")

    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large")

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    # Delete old profile picture if exists
    if current_user.get("profile_picture"):
        old_path = current_user["profile_picture"].lstrip("/")
        if os.path.exists(old_path):
            os.remove(old_path)

    with open(filepath, "wb") as f:
        f.write(contents)

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"profile_picture": f"/{filepath}", "updated_at": datetime.utcnow()}}
    )
    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    return UserResponse.model_validate(updated_user)


@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Get user preferences."""
    preferences = await db.preferences.find_one({"user_id": current_user["_id"]})
    if not preferences:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preferences not found")
    return UserPreferencesResponse.model_validate(preferences)


@router.put("/me/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: UserPreferencesCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Create or update user preferences."""
    existing = await db.preferences.find_one({"user_id": current_user["_id"]})
    update_fields = preferences_data.model_dump(exclude_unset=True)
    update_fields["updated_at"] = datetime.utcnow()

    if existing:
        await db.preferences.update_one(
            {"user_id": current_user["_id"]},
            {"$set": update_fields}
        )
    else:
        update_fields["user_id"] = current_user["_id"]
        update_fields["created_at"] = datetime.utcnow()
        await db.preferences.insert_one(update_fields)

    preferences = await db.preferences.find_one({"user_id": current_user["_id"]})
    return UserPreferencesResponse.model_validate(preferences)