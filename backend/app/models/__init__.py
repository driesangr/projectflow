"""Import all models so Alembic autogenerate can detect them."""

from app.models.base import Base, SoftDeleteMixin, TimestampMixin  # noqa: F401
from app.models.project_group import ProjectGroup  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.project import Project, MaturityLevel, ProjectStatus  # noqa: F401
from app.models.sprint import Sprint  # noqa: F401
from app.models.topic import Topic, TopicPriority  # noqa: F401
from app.models.deliverable import Deliverable, DeliverableStatus  # noqa: F401
from app.models.user_story import UserStory, UserStoryStatus  # noqa: F401
from app.models.bug import Bug, BugStatus  # noqa: F401
from app.models.task import Task, TaskStatus  # noqa: F401
from app.models.comment import Comment  # noqa: F401
from app.models.link import Link  # noqa: F401
from app.models.audit_log import AuditLog, AuditAction  # noqa: F401

__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "ProjectGroup",
    "User",
    "Project",
    "MaturityLevel",
    "ProjectStatus",
    "Sprint",
    "Topic",
    "TopicPriority",
    "Deliverable",
    "DeliverableStatus",
    "UserStory",
    "UserStoryStatus",
    "Bug",
    "BugStatus",
    "Task",
    "TaskStatus",
    "Comment",
    "Link",
    "AuditLog",
    "AuditAction",
]
