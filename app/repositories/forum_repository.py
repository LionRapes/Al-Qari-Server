"""Forum repository for YDB data extraction, query queries, and database transactions."""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.forum import *
from app.schemas.forum_schemas import *


class ForumRepository:
    """
    Repository for managing forum data in YDB.

    Attributes:
        db: An instance of the YDB database connector.
    """

    def __init__(self, db):
        """
        Initializes the repository with a database connection.
        Args:
            db: The database driver or connection object.
        """
        self.db = db

    def get_categories(self) -> list[dict[str, Any]]:
        """
        Retrieves all forum categories sorted by creation date descending.
                """
        query = """
        SELECT id, title, slug, description, created_at
        FROM categories
        ORDER BY created_at DESC;
        """
        return self.db.execute(query) or []

    def get_category(self, category_id: str) -> dict[str, Any] | None:
        """
        Retrieves a single category by its ID.
        Args:
            category_id: The ID of the category.
        """
        query = """
        DECLARE $category_id AS Utf8;
        SELECT id, title, slug, description, created_at
        FROM categories
        WHERE id = $category_id;
        """
        result = self.db.execute(query, {"$category_id": category_id})
        return result[0] if result and len(result) > 0 else None

    def get_topics(self, category_id: str, cursor: str | None, limit: int) -> list[dict[str, Any]]:
        """
        Fetches a paginated list of topics for a specific category.
        Args:
            category_id: The ID of the category.
            cursor: ISO timestamp string for pagination.
            limit: Maximum number of records to return.
        """
        query = """
        DECLARE $category_id AS Utf8;
        DECLARE $limit AS Uint32;
        DECLARE $cursor AS Timestamp;

        SELECT id, category_id, user_id, title, content_markdown, views_count, is_pinned, is_locked, created_at, updated_at
        FROM topics
        WHERE category_id = $category_id AND created_at < $cursor
        ORDER BY created_at DESC
        LIMIT $limit;
        """
        if cursor:
            cursor_val = datetime.fromisoformat(cursor)
        else:
            cursor_val = datetime.now(timezone.utc)

        params = {
            "$category_id": category_id,
            "$limit": limit,
            "$cursor": cursor_val
        }
        
        return self.db.execute(query, params) or []

    def get_topic(self, topic_id: str) -> dict[str, Any] | None:
        """
        Retrieves a single topic by its ID.

        Args:
            topic_id: The ID of the topic.
        """
        query = """
        DECLARE $topic_id AS Utf8;
        SELECT id, category_id, user_id, title, content_markdown, views_count, is_pinned, is_locked, created_at, updated_at
        FROM topics
        WHERE id = $topic_id;
        """

        result = self.db.execute(query, {"$topic_id": topic_id})
        return result[0] if result and len(result) > 0 else None

    def create_topic(self, category_id: str, user_id: str, topic_in: TopicCreateRequest) -> None:
        """
        Creates a new topic in a category.

        Args:
            category_id: The ID of the category where the topic is created.
            user_id: The ID of the user creating the topic.
            topic_in: The data request containing topic details.
        """
        topic_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        query = """
        DECLARE $id AS Utf8;
        DECLARE $category_id AS Utf8;
        DECLARE $user_id AS Utf8;
        DECLARE $title AS Utf8;
        DECLARE $content_markdown AS Utf8;
        DECLARE $views_count AS Uint64;
        DECLARE $is_pinned AS Bool;
        DECLARE $is_locked AS Bool;
        DECLARE $created_at AS Timestamp;
        DECLARE $updated_at AS Timestamp;

        UPSERT INTO topics (id, category_id, user_id, title, content_markdown, views_count, is_pinned, is_locked, created_at, updated_at)
        VALUES ($id, $category_id, $user_id, $title, $content_markdown, $views_count, $is_pinned, $is_locked, $created_at, $updated_at);
        """
        params = {
            "$id": topic_id,
            "$category_id": category_id,
            "$user_id": user_id,
            "$title": topic_in.title,
            "$content_markdown": topic_in.content,
            "$views_count": 0,
            "$is_pinned": False,
            "$is_locked": False,
            "$created_at": now,
            "$updated_at": now
        }

        self.db.execute(query, params)

    def update_topic_moderation(self, topic_id: str, moderator_id: str, mod_action: TopicModerateRequest) -> None:
        """
        Updates topic moderation status and logs the action.

        Args:
            topic_id: The ID of the topic.
            moderator_id: The ID of the moderator performing the action.
            mod_action: The moderation request containing flags and reasons.
        """
        now = datetime.now(timezone.utc)
        log_id = str(uuid.uuid4())
        action_type = "lock_update" if mod_action.is_locked is not None else "pin_update"

        query = """
        DECLARE $topic_id AS Utf8;
        DECLARE $is_locked AS Bool;
        DECLARE $is_pinned AS Bool;
        DECLARE $updated_at AS Timestamp;

        DECLARE $log_id AS Utf8;
        DECLARE $moderator_id AS Utf8;
        DECLARE $target_type AS Utf8;
        DECLARE $action AS Utf8;
        DECLARE $reason AS Utf8;

        UPDATE topics
        SET is_locked = $is_locked, is_pinned = $is_pinned, updated_at = $updated_at
        WHERE id = $topic_id;

        UPSERT INTO moderation_logs (id, moderator_id, target_type, target_id, action, reason, created_at)
        VALUES ($log_id, $moderator_id, $target_type, $topic_id, $action, $reason, $updated_at);
        """
        params = {
            "$topic_id": topic_id,
            "$is_locked": mod_action.is_locked,
            "$is_pinned": mod_action.is_pinned,
            "$updated_at": now,
            "$log_id": log_id,
            "$moderator_id": moderator_id,
            "$target_type": "topic",
            "$action": action_type,
            "$reason": getattr(mod_action, "reason", "Moderator action executed")
        }

        self.db.execute(query, params)

    def get_posts(self, topic_id: str, cursor: str | None, limit: int) -> list[dict[str, Any]]:
        """
        Fetches a paginated list of posts for a specific topic.

        Args:
            topic_id: The ID of the topic.
            cursor: ISO timestamp string for pagination.
            limit: Maximum number of records to return.
        """
        query = """
        DECLARE $topic_id AS Utf8;
        DECLARE $limit AS Uint32;
        DECLARE $cursor AS Timestamp;

        SELECT id, topic_id, user_id, parent_post_id, content_markdown, is_edited, edited_at, edited_by, created_at
        FROM posts
        WHERE topic_id = $topic_id AND created_at > $cursor
        ORDER BY created_at ASC
        LIMIT $limit;
        """
        if cursor:
            cursor_val = datetime.fromisoformat(cursor)
        else:
            cursor_val = datetime.now(timezone.utc)
        params = {
            "$topic_id": topic_id,
            "$limit": limit,
            "$cursor": cursor_val
        }

        return self.db.execute(query, params)

    def get_post(self, post_id: str) -> dict[str, Any] | None:
        """
        Retrieves a single post by its ID.

        Args:
            post_id: The ID of the post.
        """
        query = """
        DECLARE $post_id AS Utf8;
        SELECT id, topic_id, user_id, parent_post_id, content_markdown, is_edited, edited_at, edited_by, created_at
        FROM posts
        WHERE id = $post_id;
        """
        result =  self.db.execute(query, {"$post_id": post_id})
        return result[0] if result and len(result) > 0 else None

    def create_post(self, topic_id: str, user_id: str, post_in: PostCreateRequest) -> None:
        """
        Creates a new post in a topic.

        Args:
            topic_id: The ID of the topic.
            user_id: The ID of the user creating the post.
            post_in: The data request containing post details.
        """
        post_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        query = """
        DECLARE $id AS Utf8;
        DECLARE $topic_id AS Utf8;
        DECLARE $user_id AS Utf8;
        DECLARE $parent_post_id AS Utf8?;
        DECLARE $content_markdown AS Utf8;
        DECLARE $is_edited AS Bool;
        DECLARE $created_at AS Timestamp;

        UPSERT INTO posts (id, topic_id, user_id, parent_post_id, content_markdown, is_edited, created_at)
        VALUES ($id, $topic_id, $user_id, $parent_post_id, $content_markdown, $is_edited, $created_at);
        """
        params = {
            "$id": post_id,
            "$topic_id": topic_id,
            "$user_id": user_id,
            "$parent_post_id": getattr(post_in, "parent_post_id", None),
            "$content_markdown": post_in.content,
            "$is_edited": False,
            "$created_at": now
        }

        self.db.execute(query, params)

    def update_post(self, post_id: str, editor_id: str, post_update: PostUpdateRequest) -> None:
        """
        Updates the content of a post and marks it as edited.

        Args:
            post_id: The ID of the post.
            editor_id: The ID of the user editing the post.
            post_update: The data request containing updated content.
        """
        now = datetime.now(timezone.utc)
        query = """
        DECLARE $post_id AS Utf8;
        DECLARE $content_markdown AS Utf8;
        DECLARE $is_edited AS Bool;
        DECLARE $edited_at AS Timestamp;
        DECLARE $edited_by AS Utf8;

        UPDATE posts
        SET content_markdown = $content_markdown, is_edited = $is_edited, edited_at = $edited_at, edited_by = $edited_by
        WHERE id = $post_id;
        """
        params = {
            "$post_id": post_id,
            "$content_markdown": post_update.content,
            "$is_edited": True,
            "$edited_at": now,
            "$edited_by": editor_id
        }

        self.db.execute(query, params)

