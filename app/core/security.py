"""Security utilities for JSON Web Token creation and decoding."""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from app.core.config import JWT_SETTINGS


def create_access_token(user_id: str):
    """Generates a JWT access token with a 7-day expiration for a given user ID."""
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, JWT_SETTINGS.JWT_SECRET_KEY, algorithm=JWT_SETTINGS.ALGORITHM)


def decode_access_token(token: str) -> str:
    """Decodes and validates a JWT access token, returning the associated user ID."""
    try:
        payload = jwt.decode(token, JWT_SETTINGS.JWT_SECRET_KEY, algorithms=[JWT_SETTINGS.ALGORITHM])
        user_id: str | None = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
