"""API routes for user authentication, profile management, and avatar uploads."""

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps.auth import CURRENT_USER
from app.api.deps.services import USER_SERVICE
from app.schemas.user_schemas import (
    AvatarUploadResponse,
    EmailRequest,
    TokenVerifyRequest,
    TokenVerifyResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

UPLOAD_FILE = File(...)


@router.post("/auth/magic-link", summary="Request magic link for email", status_code=status.HTTP_204_NO_CONTENT)
async def request_magic_link(req: EmailRequest, service: UserService = USER_SERVICE):
    """Requests a magic link for the provided email address."""
    service.request_magic_link(req.email, req.lang)


@router.post("/auth/verify", summary="Verify magic link and login/register", response_model=TokenVerifyResponse)
async def verify_magic_link(req: TokenVerifyRequest, service: UserService = USER_SERVICE):
    """Verifies a magic link token and authenticates or registers the user."""
    return service.verify_magic_link(req.token)


@router.get("/{user_id}", summary="Get user profile", response_model=UserResponse)
async def get_user(user_id: str, service: UserService = USER_SERVICE):
    """Retrieves a user's profile by ID."""
    return service.get_user_profile(user_id)


@router.patch("/{user_id}", summary="Update user profile", status_code=status.HTTP_204_NO_CONTENT)
async def update_user(
    user_id: str,
    data: UserUpdateRequest,
    current_user_id: str = CURRENT_USER,
    service: UserService = USER_SERVICE,
):
    """Updates a user's profile information."""
    service.update_user_profile(user_id, current_user_id, data.username)


@router.post(
    "/{user_id}/avatar",
    summary="Upload user avatar",
    response_model=AvatarUploadResponse,
)
async def upload_avatar(
    user_id: str,
    file: UploadFile = UPLOAD_FILE,
    current_user_id: str = CURRENT_USER,
    service: UserService = USER_SERVICE,
):
    """Uploads and updates a user's avatar image."""
    file_content = await file.read()
    return await service.upload_user_avatar(user_id, current_user_id, file_content)


@router.delete("/{user_id}", summary="Delete user profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user_id: str = CURRENT_USER,
    service: UserService = USER_SERVICE,
):
    """Deletes a user's profile."""
    service.delete_user_profile(user_id, current_user_id)
