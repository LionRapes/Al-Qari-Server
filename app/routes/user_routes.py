from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from pydantic import BaseModel, EmailStr

from app.dependencies import get_user_service
from app.services.user_service import UserService
from app.utils import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

class EmailRequest(BaseModel):
    email: EmailStr
    lang: str

class TokenVerify(BaseModel):
    token: str
    
class UserUpdate(BaseModel):
    username: str


@router.post("/auth/magic-link", summary="Request magic link for email")
async def request_magic_link(
    req: EmailRequest,
    service: UserService = Depends(get_user_service)
):
    return service.request_magic_link(req.email, req.lang)


@router.post("/auth/verify", summary="Verify magic link and login/register")
async def verify_magic_link(
    req: TokenVerify, 
    service: UserService = Depends(get_user_service)
):
    return service.verify_magic_link(req.token)


@router.get("/{user_id}", summary="Get user profile")
async def get_user(
    user_id: str, 
    service: UserService = Depends(get_user_service)
):
    return service.get_user_profile(user_id)


@router.patch("/{user_id}", summary="Update user profile")
async def update_user(
    user_id: str, 
    data: UserUpdate, 
    current_user_id: str = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    return service.update_user_profile(user_id, current_user_id, data.username)


@router.post("/{user_id}/avatar", summary="Upload user avatar")
async def upload_avatar(
    user_id: str,
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    file_content = await file.read()
    return await service.upload_user_avatar(user_id, current_user_id, file_content)


@router.delete("/{user_id}", summary="Delete user profile", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str, 
    current_user_id: str = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    service.delete_user_profile(user_id, current_user_id)
