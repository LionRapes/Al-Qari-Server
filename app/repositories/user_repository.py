"""Repository module for managing users, and share magic links in YDB."""

import uuid
from typing import Any

import ydb

from app.core.interfaces import YdbInterface


class UserRepository:
    """Repository for managing user data and authentication magic links in YDB."""

    def __init__(self, db: YdbInterface):
        """Initializes the repository with a YDB database interface."""
        self.db = db

    def create_magic_link(self, token: str, email: str) -> None:
        """Creates a new magic link with a 15-minute expiration time."""
        query = """
        DECLARE $token AS Utf8;
        DECLARE $email AS Utf8;
        
        INSERT INTO magic_links (token, email, expires_at) 
        VALUES ($token, $email, CurrentUtcTimestamp() + Interval("PT15M"));
        """
        try:
            self.db.execute(query, {"$token": token, "$email": email})
        except ydb.Error as e:
            print(e)

    def get_magic_link(self, token: str) -> dict[str, Any] | None:
        """Retrieves the email for a valid, non-expired magic link token."""
        query = """
        DECLARE $token AS Utf8;
        
        SELECT
            token,
            email,
            expires_at
        FROM magic_links 
        WHERE token = $token AND expires_at > CurrentUtcTimestamp();
        """
        result = self.db.execute(query, {"$token": token})
        return result[0] if result else None

    def delete_magic_link(self, token: str) -> None:
        """Deletes a magic link record by its token."""
        query = "DECLARE $token AS Utf8; DELETE FROM magic_links WHERE token = $token;"
        self.db.execute(query, {"$token": token})

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Retrieves complete user details by their email."""
        query = """
        DECLARE $email AS Utf8;
        
        SELECT 
            id, 
            email, 
            username, 
            created_at, 
            avatar_url, 
            role,
            is_banned
        FROM users
        WHERE email = $email;
        """
        result = self.db.execute(query, {"$email": email})
        return result[0] if result else None

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Retrieves complete user details by their unique user ID."""
        query = """
        DECLARE $id AS Utf8;
        
        SELECT 
            id, 
            email, 
            username, 
            created_at, 
            avatar_url, 
            role,
            is_banned
        FROM users 
        WHERE id = $id;
        """
        result = self.db.execute(query, {"$id": user_id})
        return result[0] if result else None

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """Retrieves complete user details by their username."""
        query = """
        DECLARE $username AS Utf8;
        
        SELECT 
            id, 
            email, 
            username, 
            created_at, 
            avatar_url, 
            role,
            is_banned
        FROM users 
        WHERE username = $username;
        """
        result = self.db.execute(query, {"$username": username})
        return result[0] if result else None

    def create_user(self, user_id: str, email: str, username: str, role: str = "user") -> None:
        """Creates a new user record with the current UTC timestamp."""
        query = """
        DECLARE $id AS Utf8;
        DECLARE $email AS Utf8;
        DECLARE $username AS Utf8;
        DECLARE $role AS Utf8;
        
        INSERT INTO users (id, email, username, created_at, role, is_banned) 
        VALUES ($id, $email, $username, CurrentUtcTimestamp(), $role, false);
        """
        self.db.execute(query, {"$id": user_id, "$email": email, "$username": username, "$role": role})

    def update_username(self, user_id: str, username: str) -> None:
        """Updates the username for a specified user ID."""
        query = """
        DECLARE $id AS Utf8;
        DECLARE $username AS Utf8;
        
        UPDATE users SET username = $username WHERE id = $id;
        """
        self.db.execute(query, {"$id": user_id, "$username": username})

    def update_avatar(self, user_id: str, avatar_url: str) -> None:
        """Updates the avatar URL for a specified user ID."""
        query = """
        DECLARE $id AS Utf8;
        DECLARE $avatar_url AS Utf8;
        
        UPDATE users SET avatar_url = $avatar_url WHERE id = $id;
        """
        self.db.execute(query, {"$id": user_id, "$avatar_url": avatar_url})

    def delete_user(self, user_id: str) -> None:
        """Deletes a user record by their unique user ID."""
        query = "DECLARE $id AS Utf8; DELETE FROM users WHERE id = $id;"
        self.db.execute(query, {"$id": user_id})

    def set_ban_status(self, user_id: str, banned: bool, moderator_id: str, reason: str, action: str) -> None:
        """Sets user's ban status and logs the moderation action."""
        log_id = str(uuid.uuid4())

        query = """
        DECLARE $user_id AS Utf8;
        DECLARE $banned AS Bool;
        
        DECLARE $log_id AS Utf8;
        DECLARE $moderator_id AS Utf8;
        DECLARE $target_type AS Utf8;
        DECLARE $action AS Utf8;
        DECLARE $reason AS Utf8;

        -- Update the ban status
        UPDATE users
        SET is_banned = $banned
        WHERE id = $user_id;

        -- Log the moderation action
        UPSERT INTO moderation_logs (id, moderator_id, target_type, target_id, action, reason, created_at)
        VALUES ($log_id, $moderator_id, $target_type, $user_id, $action, $reason, CurrentUtcTimestamp());
        """

        params = {
            "$user_id": user_id,
            "$banned": banned,
            "$log_id": log_id,
            "$moderator_id": moderator_id,
            "$target_type": "user",
            "$action": action,
            "$reason": reason,
        }

        self.db.execute(query, params)
