from typing import Any

import ydb

from app.interfaces import YdbInterface


class UserRepository:
    def __init__(self, db: YdbInterface):
        self.db = db

    def create_magic_link(self, token: str, email: str) -> None:
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
        query = """
        DECLARE $token AS Utf8;
        SELECT email FROM magic_links 
        WHERE token = $token AND expires_at > CurrentUtcTimestamp();
        """
        result = self.db.execute(query, {"$token": token})
        return result[0] if result else None

    def delete_magic_link(self, token: str) -> None:
        query = "DECLARE $token AS Utf8; DELETE FROM magic_links WHERE token = $token;"
        self.db.execute(query, {"$token": token})

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        query = "DECLARE $email AS Utf8; SELECT id, username FROM users WHERE email = $email;"
        result = self.db.execute(query, {"$email": email})
        return result[0] if result else None

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        query = """
        DECLARE $id AS Utf8;
        SELECT id, email, username, created_at, avatar_url FROM users WHERE id = $id;
        """
        result = self.db.execute(query, {"$id": user_id})
        return result[0] if result else None

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        query = "DECLARE $username AS Utf8; SELECT id FROM users WHERE username = $username;"
        result = self.db.execute(query, {"$username": username})
        return result[0] if result else None

    def create_user(self, user_id: str, email: str, username: str) -> None:
        query = """
        DECLARE $id AS Utf8; DECLARE $email AS Utf8; DECLARE $username AS Utf8;
        INSERT INTO users (id, email, username, created_at) 
        VALUES ($id, $email, $username, CurrentUtcTimestamp());
        """
        self.db.execute(query, {
            "$id": user_id,
            "$email": email,
            "$username": username
        })

    def update_username(self, user_id: str, username: str) -> None:
        query = """
        DECLARE $id AS Utf8;
        DECLARE $username AS Utf8;
        UPDATE users SET username = $username WHERE id = $id;
        """
        self.db.execute(query, {
            "$id": user_id,
            "$username": username
        })

    def update_avatar(self, user_id: str, avatar_url: str) -> None:
        query = """
        DECLARE $id AS Utf8;
        DECLARE $avatar_url AS Utf8;
        UPDATE users SET avatar_url = $avatar_url WHERE id = $id;
        """
        self.db.execute(query, {"$id": user_id, "$avatar_url": avatar_url})

    def delete_user(self, user_id: str) -> None:
        query = "DECLARE $id AS Utf8; DELETE FROM users WHERE id = $id;"
        self.db.execute(query, {"$id": user_id})