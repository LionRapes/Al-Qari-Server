"""Schemas for forum operations including topics, posts, and moderation actions."""

from pydantic import BaseModel, Field

from app.schemas.common_schemas import Owner

# REQUEST BODY


class TopicCreateRequest(BaseModel):
    """Schema for creating a new forum topic."""
    title: str = Field(..., min_length=3, max_length=150, description="The title of the topic.")
    content: str = Field(..., min_length=10, max_length=20000, description="Markdown body content.")


class TopicModerateRequest(BaseModel):
    """Schema for updating moderation status of a topic."""
    is_locked: bool | None = None
    is_pinned: bool | None = None
    reason: str | None = Field(None, max_length=255, description="Internal reason for moderation log.")


class PostCreateRequest(BaseModel):
    """Schema for creating a new post."""
    content: str = Field(..., min_length=5, max_length=10000, description="Markdown reply content.")
    parent_post_id: str | None = None


class PostUpdateRequest(BaseModel):
    """Schema for updating an existing post."""
    content: str = Field(..., min_length=5, max_length=10000, description="Updated Markdown reply content.")


# RESPONSES

class CategoryResponse(BaseModel):
    """Schema for category details."""
    id: str
    title: str
    slug: str
    description: str
    created_at: int
    is_restricted: bool = False


class TopicResponse(BaseModel):
    """Schema for full topic details."""
    id: str
    category_id: str
    title: str
    views_count: int
    is_pinned: bool
    is_locked: bool
    created_at: int
    updated_at: int
    owner: Owner | None = None


class PaginatedTopicsResponse(BaseModel):
    """Schema for a paginated list of topics."""
    items: list[TopicResponse]
    next_cursor: int | None


class PostResponse(BaseModel):
    """Schema for post details."""
    id: str
    topic_id: str
    parent_post_id: str | None
    content_markdown: str
    is_edited: bool
    edited_at: int | None
    edited_by: str | None
    created_at: int
    owner: Owner | None = None


class PaginatedPostsResponse(BaseModel):
    """Schema for a paginated list of posts."""
    items: list[PostResponse]
    next_cursor: int | None

