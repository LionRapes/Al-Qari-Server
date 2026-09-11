"""Forum repository for YDB data extraction, query queries, and database transactions."""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.forum import *
from app.models.user import User
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
        SELECT 
            id, 
            title, 
            slug, 
            description, 
            created_at, 
            is_restricted
        
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
        
        SELECT 
            id, 
            title, 
            slug, 
            description, 
            created_at, 
            is_restricted
        
        FROM categories
        WHERE id = $category_id;
        """
        result = self.db.execute(query, {"$category_id": category_id})
        return result[0] if result and len(result) > 0 else None

    def get_topics(self, category_id: str, cursor: int | None, limit: int) -> list[dict[str, Any]]:
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

        SELECT 
            t.id AS id,
            t.category_id AS category_id,
            t.user_id AS user_id,
            t.title AS title,
            t.views_count AS views_count,
            t.is_pinned AS is_pinned,
            t.is_locked AS is_locked,
            t.created_at AS created_at,
            t.updated_at AS updated_at,

            CASE 
                WHEN u.id IS NULL THEN NULL
                ELSE AsStruct(
                    u.id AS id,
                    u.username AS username,
                    u.avatar_url AS avatar_url
                )
            END AS owner
            
        FROM topics AS t
        LEFT JOIN users AS u ON t.user_id = u.id
        WHERE t.category_id = $category_id AND t.created_at < $cursor
        ORDER BY t.created_at DESC
        LIMIT $limit;
        """
        if cursor:
            cursor_val = datetime.fromtimestamp(cursor / 1_000_000, tz=timezone.utc)
        else:
            cursor_val = datetime.now(timezone.utc)

        params = {"$category_id": category_id, "$limit": limit, "$cursor": cursor_val}

        return self.db.execute(query, params) or []

    def get_topic(self, topic_id: str) -> dict[str, Any] | None:
        """
        Retrieves a single topic by its ID.

        Args:
            topic_id: The ID of the topic.
        """
        query = """
        DECLARE $topic_id AS Utf8;

        SELECT 
            t.id AS id,
            t.category_id AS category_id,
            t.user_id AS user_id,
            t.title AS title,
            t.views_count AS views_count,
            t.is_pinned AS is_pinned,
            t.is_locked AS is_locked,
            t.created_at AS created_at,
            t.updated_at AS updated_at,

            CASE 
                WHEN u.id IS NULL THEN NULL
                ELSE AsStruct(
                    u.id AS id,
                    u.username AS username,
                    u.avatar_url AS avatar_url
                )
            END AS owner
            
        FROM topics AS t
        LEFT JOIN users AS u ON t.user_id = u.id
        WHERE t.id = $topic_id;
        """

        result = self.db.execute(query, {"$topic_id": topic_id})
        return result[0] if result and len(result) > 0 else None

    def create_topic(self, category_id: str, user: User, req: TopicCreateRequest) -> None:
        """
        Creates a new topic in a category.

        Args:
            category_id: The ID of the category where the topic is created.
            user_id: The ID of the user creating the topic.
            req: The data request containing topic details.
        """
        topic_id = str(uuid.uuid4())
        post_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        query = """
        DECLARE $topic_id AS Utf8;
        DECLARE $category_id AS Utf8;
        DECLARE $user_id AS Utf8;
        DECLARE $title AS Utf8;
        DECLARE $views_count AS Uint64;
        DECLARE $is_pinned AS Bool;
        DECLARE $is_locked AS Bool;
        DECLARE $created_at AS Timestamp;
        DECLARE $updated_at AS Timestamp;

        DECLARE $post_id AS Utf8;
        DECLARE $content_markdown AS Utf8;
        DECLARE $post_created_at AS Timestamp;

        -- Create topic
        UPSERT INTO topics (
            id, category_id, user_id, title,
            views_count, is_pinned, is_locked,
            created_at, updated_at
        )
        VALUES (
            $topic_id, $category_id, $user_id, $title,
            $views_count, $is_pinned, $is_locked,
            $created_at, $updated_at
        );

        -- Create first post
        UPSERT INTO posts (
            id, topic_id, user_id, parent_post_id,
            content_markdown, is_edited, edited_at, edited_by,
            created_at
        )
        VALUES (
            $post_id, $topic_id, $user_id, CAST(NULL AS Utf8),
            $content_markdown, false, CAST(NULL AS Timestamp), CAST(NULL AS Utf8),
            $post_created_at
        );
        """

        params = {
            "$topic_id": topic_id,
            "$category_id": category_id,
            "$user_id": user.id,
            "$title": req.title,
            "$views_count": 0,
            "$is_pinned": False,
            "$is_locked": False,
            "$created_at": now,
            "$updated_at": now,

            "$post_id": post_id,
            "$content_markdown": req.content,
            "$post_created_at": now,
        }

        self.db.execute(query, params)


    def update_topic_moderation(self, topic_id: str, moderator_id: str, req: TopicModerateRequest) -> None:
        """
        Updates topic moderation status and logs the action.

        Args:
            topic_id: The ID of the topic.
            moderator_id: The ID of the moderator performing the action.
            req: The moderation request containing flags and reasons.
        """
        topic = self.get_topic(topic_id)
        
        is_locked = req.is_locked if req.is_locked is not None else topic.is_locked
        is_pinned = req.is_pinned if req.is_pinned is not None else topic.is_pinned
        reason = req.reason or "Moderator action executed"
        
        now = datetime.now(timezone.utc)
        log_id = str(uuid.uuid4())
        
        actions = []
        if req.is_locked is not None:
            actions.append("lock_update")
        if req.is_pinned is not None:
            actions.append("pin_update")

        action_type = ",".join(actions) if actions else "noop"

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

        UPDATE topics SET 
            is_locked = $is_locked, 
            is_pinned = $is_pinned, 
            updated_at = $updated_at
        WHERE id = $topic_id;
        
        UPSERT INTO moderation_logs (id, moderator_id, target_type, target_id, action, reason, created_at)
        VALUES ($log_id, $moderator_id, $target_type, $topic_id, $action, $reason, $updated_at);
        """
        params = {
            "$topic_id": topic_id,
            "$is_locked": is_locked,
            "$is_pinned": is_pinned,
            "$updated_at": now,
            "$log_id": log_id,
            "$moderator_id": moderator_id,
            "$target_type": "topic",
            "$action": action_type,
            "$reason": reason,
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

        SELECT 
            p.id AS id,
            p.topic_id AS topic_id,
            p.user_id AS user_id,
            p.parent_post_id AS parent_post_id,
            p.content_markdown AS content_markdown,
            p.is_edited AS is_edited,
            p.edited_at AS edited_at,
            p.edited_by AS edited_by,
            p.created_at AS created_at,

            CASE 
                WHEN u.id IS NULL THEN NULL
                ELSE AsStruct(
                    u.id AS id,
                    u.username AS username,
                    u.avatar_url AS avatar_url
                )
            END AS owner
            
        FROM posts AS p
        LEFT JOIN users AS u ON p.user_id = u.id
        WHERE p.topic_id = $topic_id AND p.created_at < $cursor
        ORDER BY p.created_at ASC
        LIMIT $limit;
        """
        if cursor:
            cursor_val = datetime.fromtimestamp(cursor / 1_000_000, tz=timezone.utc)
        else:
            cursor_val = datetime.now(timezone.utc)
        params = {"$topic_id": topic_id, "$limit": limit, "$cursor": cursor_val}

        return self.db.execute(query, params)

    def get_post(self, post_id: str) -> dict[str, Any] | None:
        """
        Retrieves a single post by its ID.

        Args:
            post_id: The ID of the post.
        """
        query = """
        DECLARE $post_id AS Utf8;

        SELECT 
            p.id AS id,
            p.topic_id AS topic_id,
            p.user_id AS user_id,
            p.parent_post_id AS parent_post_id,
            p.content_markdown AS content_markdown,
            p.is_edited AS is_edited,
            p.edited_at AS edited_at,
            p.edited_by AS edited_by,
            p.created_at AS created_at,

            CASE 
                WHEN u.id IS NULL THEN NULL
                ELSE AsStruct(
                    u.id AS id,
                    u.username AS username,
                    u.avatar_url AS avatar_url
                )
            END AS owner
            
        FROM posts AS p
        LEFT JOIN users AS u ON p.user_id = u.id
        WHERE p.id = $post_id;
        """
        result = self.db.execute(query, {"$post_id": post_id})
        return result[0] if result and len(result) > 0 else None

    def create_post(self, topic_id: str, user_id: str, req: PostCreateRequest) -> None:
        """
        Creates a new post in a topic.

        Args:
            topic_id: The ID of the topic.
            user_id: The ID of the user creating the post.
            req: The data request containing post details.
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
            "$parent_post_id": getattr(req, "parent_post_id", None),
            "$content_markdown": req.content,
            "$is_edited": False,
            "$created_at": now,
        }

        self.db.execute(query, params)

    def update_post(self, post_id: str, editor_id: str, req: PostUpdateRequest) -> None:
        """
        Updates the content of a post and marks it as edited.

        Args:
            post_id: The ID of the post.
            editor_id: The ID of the user editing the post.
            req: The data request containing updated content.
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
            "$content_markdown": req.content,
            "$is_edited": True,
            "$edited_at": now,
            "$edited_by": editor_id,
        }

        self.db.execute(query, params)
    
    def delete_post(self, post_id: str, moderator_id: str, reason: str) -> None:
        """
        Deletes a post from the database and logs the moderation action.

        Args:
            post_id: The ID of the post to delete.
            moderator_id: The ID of the moderator performing the action.
            reason: The reason for the deletion.
        """
        log_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        query = """
        DECLARE $post_id AS Utf8;
        
        DECLARE $log_id AS Utf8;
        DECLARE $moderator_id AS Utf8;
        DECLARE $target_type AS Utf8;
        DECLARE $action AS Utf8;
        DECLARE $reason AS Utf8;
        DECLARE $created_at AS Timestamp;

        -- Delete the post
        DELETE FROM posts
        WHERE id = $post_id;

        -- Log the moderation action
        UPSERT INTO moderation_logs (id, moderator_id, target_type, target_id, action, reason, created_at)
        VALUES ($log_id, $moderator_id, $target_type, $post_id, $action, $reason, $created_at);
        """
        
        params = {
            "$post_id": post_id,
            "$log_id": log_id,
            "$moderator_id": moderator_id,
            "$target_type": "post",
            "$action": "delete",
            "$reason": reason,
            "$created_at": now,
        }

        self.db.execute(query, params)


    def delete_topic(self, topic_id: str, moderator_id: str, reason: str) -> None:
        """
        Deletes a topic from YDB and logs the moderation action.

        Args:
            topic_id: The ID of the topic to delete.
            moderator_id: The ID of the moderator performing the action.
            reason: The reason for the deletion.
        """
        log_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        query = """
        DECLARE $topic_id AS Utf8;
        DECLARE $log_id AS Utf8;
        DECLARE $moderator_id AS Utf8;
        DECLARE $target_type AS Utf8;
        DECLARE $action AS Utf8;
        DECLARE $reason AS Utf8;
        DECLARE $created_at AS Timestamp;

        -- Delete the topic
        DELETE FROM topics
        WHERE id = $topic_id;

        -- Log the moderation action
        UPSERT INTO moderation_logs (id, moderator_id, target_type, target_id, action, reason, created_at)
        VALUES ($log_id, $moderator_id, $target_type, $topic_id, $action, $reason, $created_at);
        """

        params = {
            "$topic_id": topic_id,
            "$log_id": log_id,
            "$moderator_id": moderator_id,
            "$target_type": "topic",
            "$action": "delete",
            "$reason": reason,
            "$created_at": now,
        }

        self.db.execute(query, params)