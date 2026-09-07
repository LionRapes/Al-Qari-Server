from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Category(BaseModel):
    """
    Database model for YDB categories table.

    Attributes:
        id: Unique identifier of the category.
        title: Human‑readable category name.
        slug: URL‑friendly identifier for the category.
        description: Text description of the category.
        created_at: Timestamp when the category was created.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    description: str
    created_at: int


class Topic(BaseModel):
    """
    Database model for YDB topics table.

    Attributes:
        id: Unique identifier of the topic.
        category_id: Identifier of the category the topic belongs to.
        user_id: Identifier of the user who created the topic.
        title: Human‑readable topic title.
        content_markdown: Markdown content of the topic.
        views_count: Number of views the topic has received.
        is_pinned: Whether the topic is pinned.
        is_locked: Whether the topic is locked from new posts.
        created_at: Timestamp when the topic was created.
        updated_at: Timestamp when the topic was last updated.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    category_id: str
    user_id: str
    title: str
    content_markdown: str
    views_count: int
    is_pinned: bool
    is_locked: bool
    created_at: int
    updated_at: int


class Post(BaseModel):
    """
    Database model for YDB posts table.

    Attributes:
        id: Unique identifier of the post.
        topic_id: Identifier of the topic the post belongs to.
        user_id: Identifier of the user who created the post.
        parent_post_id: Identifier of the parent post (for threaded replies).
        content_markdown: Markdown content of the post.
        is_edited: Whether the post has been edited.
        edited_at: Timestamp when the post was edited.
        edited_by: Identifier of the moderator/user who edited the post.
        created_at: Timestamp when the post was created.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    topic_id: str
    user_id: str
    parent_post_id: str | None = None
    content_markdown: str
    is_edited: bool
    edited_at: int | None = None
    edited_by: str | None = None
    created_at: int


class ModerationLog(BaseModel):
    """
    Database model for YDB moderation_logs table.

    Attributes:
        id: Unique identifier of the moderation log entry.
        moderator_id: Identifier of the moderator performing the action.
        target_type: Type of entity affected (topic, post, user).
        target_id: Identifier of the affected entity.
        action: Moderation action performed.
        reason: Reason for the moderation action.
        created_at: Timestamp when the moderation action was recorded.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    moderator_id: str
    target_type: str
    target_id: str
    action: str
    reason: str
    created_at: int
