"""Forum service implementation for categories, topics, and posts."""

from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.forum_repository import ForumRepository
from app.schemas.forum_schemas import *


class ForumService:
    """Service layer for handling forum business logic, moderation, and data transformation."""

    def __init__(self, repo: ForumRepository):
        """Initialize forum service with repository dependency."""
        self.repo = repo

    def get_categories(self) -> list[CategoryResponse]:
        """Fetch all available forum categories."""
        raw_categories = self.repo.get_categories()
        return [CategoryResponse(**row) for row in raw_categories]

    def get_topics(
        self, category_id: str, cursor: str | None, limit: int
    ) -> PaginatedTopicsResponse:
        """Get topics for a specific category using cursor pagination."""
        raw_topics = self.repo.get_topics(category_id, cursor, limit)
        
        items = [TopicResponse(**topic) for topic in raw_topics]
        
        next_cursor = None
        if items and len(items) == limit:
            next_cursor = items[-1].created_at.isoformat()
            
        return PaginatedTopicsResponse(
            items=items, 
            next_cursor=next_cursor
        )

    def create_topic(
        self, category_id: str, user_id: str, req: TopicCreateRequest
    ) -> None:
        """Create a new topic with initial Markdown content."""
        category = self.repo.get_category(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        self.repo.create_topic(category_id, user_id, req)

    def moderate_topic(
        self, topic_id: str, moderator_id: str, req: TopicModerateRequest
    ) -> None:
        """Lock, unlock, pin, or unpin a topic. Restricted to moderators/admins."""
        topic = self.repo.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

        self.repo.update_topic_moderation(topic_id, moderator_id, req)

    def get_posts(
        self, topic_id: str, cursor: str | None, limit: int
    ) -> PaginatedPostsResponse:
        """Get thread replies using cursor pagination."""
        topic = self.repo.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

        raw_posts = self.repo.get_posts(topic_id, cursor, limit)
        
        items = [PostResponse(**post) for post in raw_posts]

        next_cursor = None
        if items and len(items) == limit:
            next_cursor = items[-1].created_at.isoformat()

        return PaginatedPostsResponse(
            items=items,
            next_cursor=next_cursor
        )

    def create_post(
        self, topic_id: str, user_id: str, req: PostCreateRequest
    ) -> None:
        """Reply to a topic using Markdown. Supports nested replies via parent_post_id."""
        topic = self.repo.get_topic(topic_id)
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

        if getattr(topic, "is_locked", False):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot reply to a locked topic.")

        return self.repo.create_post(topic_id, user_id, req)

    def edit_post(
        self, post_id: str, current_user: User, req: PostUpdateRequest
    ) -> None:
        """Edit an existing post. Service layer will verify if the user owns the post or is a moderator."""
        post = self.repo.get_post(post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

        is_author = getattr(post, "user_id", None) == current_user.id
        is_mod = getattr(current_user, "role", None) == 'moderator' or getattr(current_user, "role", None) == 'admin'

        if not (is_author or is_mod):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to edit this post.",
            )

        return self.repo.update_post(post_id, current_user.id, req)
