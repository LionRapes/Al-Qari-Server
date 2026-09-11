"""Forum service implementation for categories, topics, and posts."""

from fastapi import HTTPException, status

from app.core.utils import validate_optional
from app.models.forum import Post, PostDetails, Topic, TopicDetails
from app.models.user import User, UserRole
from app.repositories.forum_repository import ForumRepository
from app.schemas.forum_schemas import *


class ForumService:
    """Service layer for handling forum business logic, moderation, and data transformation."""

    def __init__(self, repo: ForumRepository):
        """Initialize forum service with repository dependency."""
        self.repo = repo

    def get_categories(self) -> list[CategoryResponse]:
        """Fetch all available forum categories."""
        return [CategoryResponse.model_validate(row) for row in self.repo.get_categories()]
    
    def get_category(self, category_id) -> CategoryResponse:
        """Fetch forum category."""
        return validate_optional(CategoryResponse, self.repo.get_category(category_id))

    def get_topics(
        self, category_id: str, cursor: int | None, limit: int
    ) -> PaginatedTopicsResponse:
        """Get topics for a specific category using cursor pagination."""
        items = [TopicDetails.model_validate(row) for row in self.repo.get_topics(category_id, cursor, limit)]
        
        next_cursor = None
        if items and len(items) == limit:
            next_cursor = items[-1].created_at
            
        return PaginatedTopicsResponse(
            items=[TopicResponse.model_validate(row.model_dump()) for row in items],
            next_cursor=next_cursor
        )
        
    def get_topic(self, topic_id: str) -> TopicResponse:
        """Fetch all available forum categories."""
        topic = validate_optional(TopicDetails, self.repo.get_topic(topic_id))
        
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found."
            )
            
        return TopicResponse.model_validate(topic.model_dump())

    def create_topic(
        self, category_id: str, current_user: User, req: TopicCreateRequest
    ) -> None:
        """Create a new topic with initial Markdown content."""
        category = validate_optional(CategoryResponse, self.repo.get_category(category_id))
        
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        if category.is_restricted and current_user.role not in UserRole.staff():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only moderators can create topics in this category."
            )
        
        if current_user.is_banned:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You're banned.")
            
        self.repo.create_topic(category_id, current_user, req)

    def moderate_topic(
        self, topic_id: str, moderator_id: str, req: TopicModerateRequest
    ) -> None:
        """Lock, unlock, pin, or unpin a topic. Restricted to moderators/admins."""
        topic = validate_optional(Topic, self.repo.get_topic(topic_id))
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

        self.repo.update_topic_moderation(topic_id, moderator_id, req)

    def get_posts(
        self, topic_id: str, cursor: int | None, limit: int
    ) -> PaginatedPostsResponse:
        """Get thread replies using cursor pagination."""
        topic = validate_optional(Topic, self.repo.get_topic(topic_id))
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

        items = [PostDetails.model_validate(row) for row in self.repo.get_posts(topic_id, cursor, limit)]

        next_cursor = None
        if items and len(items) == limit:
            next_cursor = items[-1].created_at

        return PaginatedPostsResponse(
            items=[PostResponse.model_validate(row.model_dump()) for row in items],
            next_cursor=next_cursor
        )

    def create_post(
        self, topic_id: str, current_user: User, req: PostCreateRequest
    ) -> None:
        """Reply to a topic using Markdown. Supports nested replies via parent_post_id."""
        topic = validate_optional(Topic, self.repo.get_topic(topic_id))
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

        if topic.is_locked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot reply to a locked topic.")

        if current_user.is_banned:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You're banned.")

        return self.repo.create_post(topic_id, current_user.id, req)

    def edit_post(
        self, post_id: str, current_user: User, req: PostUpdateRequest
    ) -> None:
        """Edit an existing post. Service layer will verify if the user owns the post or is a moderator."""
        post = validate_optional(Post, self.repo.get_post(post_id))
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

        if current_user.role not in UserRole.staff():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to edit this post.",
            )

        return self.repo.update_post(post_id, current_user.id, req)
    
    def delete_post(self, post_id: str, moderator_id: str, reason: str | None = None) -> None:
        """Delete a post and log the moderation action."""
        post = validate_optional(Post, self.repo.get_post(post_id))
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Post not found"
            )

        delete_reason = reason or "Post deleted by moderator"
        
        self.repo.delete_post(post_id, moderator_id, delete_reason)
        
    def delete_topic(self, topic_id: str, moderator_id: str, reason: str | None = None) -> None:
        """Deletes a topic and ensures it exists first."""
        topic = validate_optional(Topic, self.repo.get_topic(topic_id))
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found."
            )
        
        delete_reason = reason or "Topic deleted by moderator"
        self.repo.delete_topic(topic_id, moderator_id, delete_reason)
