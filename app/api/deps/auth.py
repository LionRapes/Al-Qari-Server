"""
Dependency injection providers for API routes.

This module provides FastAPI dependencies to handle authentication."""

from functools import partial

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.api.deps.repositories import get_user_repository
from app.core.security import decode_access_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

token_header = APIKeyHeader(name="X-Auth-Token", auto_error=False)

async def get_current_user(
    optional: bool = False,
    token: str | None = Depends(token_header),
) -> str:
    """
    Dependency to retrieve the current authenticated user ID from the request header.

    Args:
        optional (bool): A flag indicating whether the user ID is optional.
        token (str | None): The authentication token extracted from the request headers.

    Returns:
        str: The user ID associated with the token.

    Raises:
        HTTPException: If the token is missing or invalid (401 Unauthorized).
    """
    if not token:
        if optional:
            return None
        else: 
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

    return decode_access_token(token)


async def get_current_active_user(
    user_id: str = Depends(get_current_user),
    repo: UserRepository = Depends(get_user_repository)
) -> User:
    """
    Dependency to retrieve the full user object for the authenticated user.
    """
    user_data = repo.get_user_by_id(user_id) 
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    return User(**user_data) 


async def get_current_moderator(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to verify the current active user is a moderator.
    """
    if current_user.role not in UserRole.staff():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges."
        )
        
    return current_user


CURRENT_USER = Depends(get_current_user)
OPTIONAL_CURRENT_USER = Depends(partial(get_current_user, optional=True))
CURRENT_ACTIVE_USER = Depends(get_current_active_user)
CURRENT_MODERATOR = Depends(get_current_moderator)
