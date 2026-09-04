from typing import Any

from app.interfaces import YdbInterface


class PlaylistRepository:
    def __init__(self, db: YdbInterface):
        self.db = db

    def create_playlist(self, playlist_id: str, owner_id: str, title: str, data: str, is_public: bool) -> None:
        query = """
        DECLARE $id AS Utf8;
        DECLARE $owner_id AS Utf8;
        DECLARE $title AS Utf8;
        DECLARE $data AS Utf8;
        DECLARE $is_public AS Bool;
        
        INSERT INTO playlists (id, owner_id, title, data, is_public, created_at, updated_at) 
        VALUES ($id, $owner_id, $title, $data, $is_public, CurrentUtcTimestamp(), CurrentUtcTimestamp());
        """
        self.db.execute(query, {
            "$id": playlist_id,
            "$owner_id": owner_id,
            "$title": title,
            "$data": data,
            "$is_public": is_public
        })

    def get_playlist_by_id(self, playlist_id: str) -> dict[str, Any] | None:
        query = """
        DECLARE $id AS Utf8;
        SELECT 
            p.id, p.owner_id, p.title, p.data, p.is_public, p.forked_from_id, p.created_at, p.updated_at,
            u.username, u.avatar_url
        FROM playlists AS p
        LEFT JOIN users AS u ON p.owner_id = u.id
        WHERE p.id = $id;
        """
        result = self.db.execute(query, {"$id": playlist_id})
        return result[0] if result else None

    def get_public_playlists(self, limit: int, offset: int) -> list[dict[str, Any]]:
        query = """
        DECLARE $limit AS Uint64;
        DECLARE $offset AS Uint64;

        SELECT 
            p.id, p.owner_id, p.title, p.data, p.is_public, p.forked_from_id, p.created_at, p.updated_at,
            u.username, u.avatar_url
        FROM playlists AS p
        LEFT JOIN users AS u ON p.owner_id = u.id
        WHERE p.is_public = true
        ORDER BY p.created_at DESC
        LIMIT $limit OFFSET $offset;
        """
        return self.db.execute(query, {"$limit": limit, "$offset": offset}) or []

    def get_user_shared_playlists(self, user_id: str) -> list[dict[str, Any]]:
        query = """
        DECLARE $user_id AS Utf8;
        SELECT 
            p.id, p.owner_id AS owner_id, p.title AS title,
            p.is_public AS is_public, m.role AS role, m.added_at AS added_at,
            u.username, u.avatar_url
        FROM playlist_members AS m
        INNER JOIN playlists AS p ON m.playlist_id = p.id
        LEFT JOIN users AS u ON p.owner_id = u.id
        WHERE m.user_id = $user_id;
        """
        return self.db.execute(query, {"$user_id": user_id}) or []

    def get_user_owned_playlists(self, user_id: str) -> list[dict[str, Any]]:
        query = """
        DECLARE $user_id AS Utf8;
        SELECT 
            p.id, p.owner_id, p.title, p.data, p.is_public,
            p.forked_from_id, p.created_at, p.updated_at,
            u.username, u.avatar_url
        FROM playlists AS p
        LEFT JOIN users AS u ON p.owner_id = u.id
        WHERE p.owner_id = $user_id;
        """
        return self.db.execute(query, {"$user_id": user_id}) or []

    def search_public_playlists(self, words: list[str], limit: int) -> list[dict[str, Any]]:
        declare_statements = ["DECLARE $limit AS Uint64;"]
        where_conditions = ["p.is_public = true"] 
        params = {"$limit": limit}

        word_conditions = []
        for i, word in enumerate(words):
            param_name = f"$word_{i}"
            declare_statements.append(f"DECLARE {param_name} AS Utf8;")
            word_conditions.append(f"p.title ILIKE {param_name}")
            params[param_name] = f"%{word}%"

        if word_conditions:
            where_conditions.append(f"({" OR ".join(word_conditions)})")

        query = f"""
        {chr(10).join(declare_statements)}
        SELECT 
            p.id, p.owner_id, p.title, p.data, p.is_public, p.forked_from_id, p.created_at, p.updated_at,
            u.username, u.avatar_url
        FROM playlists AS p
        LEFT JOIN users AS u ON p.owner_id = u.id
        WHERE {" AND ".join(where_conditions)}
        ORDER BY p.created_at DESC
        LIMIT $limit;
        """
        return self.db.execute(query, params) or []

    def get_raw_playlist(self, playlist_id: str) -> dict[str, Any] | None:
        query = "DECLARE $id AS Utf8; SELECT title, data, is_public, owner_id FROM playlists WHERE id = $id;"
        result = self.db.execute(query, {"$id": playlist_id})
        return result[0] if result else None

    def update_playlist(self, playlist_id: str, title: str, data: str, is_public: bool) -> None:
        query = """
        DECLARE $id AS Utf8;
        DECLARE $title AS Utf8;
        DECLARE $data AS Utf8;
        DECLARE $is_public AS Bool;
        
        UPDATE playlists SET 
            title = $title, 
            data = $data, 
            is_public = $is_public, 
            updated_at = CurrentUtcTimestamp() 
        WHERE id = $id;
        """
        self.db.execute(query, {
            "$id": playlist_id,
            "$title": title,
            "$data": data,
            "$is_public": is_public
        })

    def delete_playlist(self, playlist_id: str) -> None:
        query = "DECLARE $id AS Utf8; DELETE FROM playlists WHERE id = $id;"
        self.db.execute(query, {"$id": playlist_id})

    def insert_forked_playlist(self, new_id: str, owner_id: str, title: str, data: str, is_public: bool, forked_from: str) -> None:
        query = """
        DECLARE $id AS Utf8; DECLARE $owner_id AS Utf8; DECLARE $title AS Utf8;
        DECLARE $data AS Utf8; DECLARE $is_public AS Bool; DECLARE $forked_from AS Utf8;
        
        INSERT INTO playlists (id, owner_id, title, data, is_public, forked_from_id, created_at, updated_at) 
        VALUES ($id, $owner_id, $title, $data, $is_public, $forked_from, CurrentUtcTimestamp(), CurrentUtcTimestamp());
        """
        self.db.execute(query, {
            "$id": new_id,
            "$owner_id": owner_id,
            "$title": title,
            "$data": data,
            "$is_public": is_public,
            "$forked_from": forked_from
        })

    def create_share_link(self, token: str, playlist_id: str, role: str, expires_in_hours: int) -> None:
        query = f"""
        DECLARE $token AS Utf8;
        DECLARE $playlist_id AS Utf8;
        DECLARE $role AS Utf8;
        
        INSERT INTO playlist_share_links (token, playlist_id, role, expires_at, created_at) 
        VALUES ($token, $playlist_id, $role, CurrentUtcTimestamp() + Interval("PT{expires_in_hours}H"), CurrentUtcTimestamp());
        """
        self.db.execute(query, {
            "$token": token,
            "$playlist_id": playlist_id,
            "$role": role
        })

    def remove_playlist_member(self, playlist_id: str, user_id: str) -> None:
        query = """
        DECLARE $playlist_id AS Utf8;
        DECLARE $user_id AS Utf8;
        DELETE FROM playlist_members 
        WHERE playlist_id = $playlist_id AND user_id = $user_id;
        """
        self.db.execute(query, {"$playlist_id": playlist_id, "$user_id": user_id})

    def get_active_share_link(self, token: str) -> dict[str, Any] | None:
        query = """
        DECLARE $token AS Utf8;
        SELECT playlist_id, role FROM playlist_share_links 
        WHERE token = $token AND expires_at > CurrentUtcTimestamp();
        """
        result = self.db.execute(query, {"$token": token})
        return result[0] if result else None

    def delete_share_link(self, token: str) -> None:
        query = "DECLARE $token AS Utf8; DELETE FROM playlist_share_links WHERE token = $token;"
        self.db.execute(query, {"$token": token})

    def get_playlist_member(self, playlist_id: str, user_id: str) -> dict[str, Any] | None:
        query = """
        DECLARE $playlist_id AS Utf8;
        DECLARE $user_id AS Utf8;
        SELECT role, added_at FROM playlist_members 
        WHERE playlist_id = $playlist_id AND user_id = $user_id;
        """
        result = self.db.execute(query, {"$playlist_id": playlist_id, "$user_id": user_id})
        return result[0] if result else None

    def update_member_role(self, playlist_id: str, user_id: str, role: str) -> None:
        query = """
        DECLARE $playlist_id AS Utf8;
        DECLARE $user_id AS Utf8;
        DECLARE $new_role AS Utf8;
        
        UPDATE playlist_members 
        SET role = $new_role 
        WHERE playlist_id = $playlist_id AND user_id = $user_id;
        """
        self.db.execute(query, {"$playlist_id": playlist_id, "$user_id": user_id, "$new_role": role})

    def add_playlist_member(self, playlist_id: str, user_id: str, role: str) -> None:
        query = """
        DECLARE $playlist_id AS Utf8;
        DECLARE $user_id AS Utf8;
        DECLARE $role AS Utf8;
        
        INSERT INTO playlist_members (playlist_id, user_id, role, added_at) 
        VALUES ($playlist_id, $user_id, $role, CurrentUtcTimestamp());
        """
        self.db.execute(query, {"$playlist_id": playlist_id, "$user_id": user_id, "$role": role})

    def get_playlist_members_list(self, playlist_id: str) -> list[dict[str, Any]]:
        query = """
        DECLARE $playlist_id AS Utf8;
        SELECT m.user_id, m.role, m.added_at, u.username, u.avatar_url
        FROM playlist_members AS m
        LEFT JOIN users AS u ON m.user_id = u.id
        WHERE m.playlist_id = $playlist_id;
        """
        return self.db.execute(query, {"$playlist_id": playlist_id}) or []