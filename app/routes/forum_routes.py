"""Forum API endpoints for managing categories and topics."""

from fastapi import APIRouter, Query, status

from app.api.deps.auth import CURRENT_ACTIVE_USER, CURRENT_MODERATOR, CURRENT_USER
from app.api.deps.services import FORUM_SERVICE
from app.models.user import User
from app.schemas.forum_schemas import (
    CategoryResponse,
    PaginatedPostsResponse,
    PaginatedTopicsResponse,
    PostCreateRequest,
    PostUpdateRequest,
    TopicCreateRequest,
    TopicModerateRequest,
)
from app.services.forum_service import ForumService

router = APIRouter(prefix="/forum", tags=["Forum"])


@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories(
    _: str = CURRENT_USER,
    service: ForumService = FORUM_SERVICE,
):
    """Fetch all available forum categories."""
    return service.get_categories()


@router.get("/categories/{category_id}/topics", response_model=PaginatedTopicsResponse)
async def get_topics(
    category_id: str,
    cursor: str | None = Query(None, description="Timestamp cursor for pagination"),
    limit: int = Query(20, ge=1, le=100),
    _: str = CURRENT_USER,
    service: ForumService = FORUM_SERVICE,
):
    """Get topics for a specific category using cursor pagination."""
    return service.get_topics(category_id, cursor, limit)


@router.post("/categories/{category_id}/topics", status_code=status.HTTP_201_CREATED)
async def create_topic(
    category_id: str,
    req: TopicCreateRequest,
    current_user_id: str = CURRENT_USER,
    service: ForumService = FORUM_SERVICE,
):
    """Create a new topic with initial Markdown content."""
    service.create_topic(category_id, current_user_id, req)


@router.patch("/topics/{topic_id}/moderate", status_code=status.HTTP_204_NO_CONTENT)
async def moderate_topic(
    topic_id: str,
    req: TopicModerateRequest,
    current_moderator: User = CURRENT_MODERATOR,
    service: ForumService = FORUM_SERVICE,
):
    """Lock, unlock, pin, or unpin a topic. Restricted to moderators/admins."""
    service.moderate_topic(topic_id, current_moderator.id, req)


@router.get("/topics/{topic_id}/posts", response_model=PaginatedPostsResponse)
async def get_posts(
    topic_id: str,
    cursor: str | None = Query(None, description="Timestamp cursor for pagination"),
    limit: int = Query(50, ge=1, le=100),
    _: str = CURRENT_USER,
    service: ForumService = FORUM_SERVICE,
):
    """Get thread replies using cursor pagination."""
    return service.get_posts(topic_id, cursor, limit)


@router.post("/topics/{topic_id}/posts", status_code=status.HTTP_201_CREATED)
async def create_post(
    topic_id: str,
    req: PostCreateRequest,
    current_user_id: str = CURRENT_USER,
    service: ForumService = FORUM_SERVICE,
):
    """Reply to a topic using Markdown. Supports nested replies via parent_post_id."""
    service.create_post(topic_id, current_user_id, req)


@router.patch("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def edit_post(
    post_id: str,
    post_update: PostUpdateRequest,
    current_user: User = CURRENT_ACTIVE_USER,
    service: ForumService = FORUM_SERVICE,
):
    """Edit an existing post. Service layer will verify if the user owns the post or is a moderator."""
    service.edit_post(post_id, current_user, post_update)
