"""
Maturity calculation service.

Maturity is expressed as a percentage (0–100) and stored directly on the
entity so the frontend can read it without re-computing on every request.

Hierarchy:
  Task → UserStory → Deliverable → Topic
         (no maturity)  maturity      maturity

  Task → Bug → Deliverable → Topic
               (via bug)
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def calculate_deliverable_maturity(
    deliverable_id: UUID, db: AsyncSession
) -> float:
    """
    Calculate and persist the maturity_percent of a Deliverable.

    Maturity = (number of Done UserStories + Done Bugs) / (total non-deleted UserStories + Bugs) * 100
    Returns the calculated percentage (0.0 if no items exist).
    """
    from app.models.deliverable import Deliverable
    from app.models.user_story import UserStory, UserStoryStatus
    from app.models.bug import Bug, BugStatus

    # Count user stories
    total_stories_result = await db.execute(
        select(func.count(UserStory.id)).where(
            UserStory.deliverable_id == deliverable_id,
            UserStory.is_deleted.is_(False),
        )
    )
    total_stories: int = total_stories_result.scalar_one()

    done_stories_result = await db.execute(
        select(func.count(UserStory.id)).where(
            UserStory.deliverable_id == deliverable_id,
            UserStory.is_deleted.is_(False),
            UserStory.status == UserStoryStatus.done,
        )
    )
    done_stories: int = done_stories_result.scalar_one()

    # Count bugs
    total_bugs_result = await db.execute(
        select(func.count(Bug.id)).where(
            Bug.deliverable_id == deliverable_id,
            Bug.is_deleted.is_(False),
        )
    )
    total_bugs: int = total_bugs_result.scalar_one()

    done_bugs_result = await db.execute(
        select(func.count(Bug.id)).where(
            Bug.deliverable_id == deliverable_id,
            Bug.is_deleted.is_(False),
            Bug.status == BugStatus.done,
        )
    )
    done_bugs: int = done_bugs_result.scalar_one()

    total = total_stories + total_bugs
    done = done_stories + done_bugs

    if total == 0:
        maturity = 0.0
    else:
        maturity = round((done / total) * 100, 2)

    # Persist the calculated value
    deliverable = await db.get(Deliverable, deliverable_id)
    if deliverable:
        deliverable.maturity_percent = maturity
        await db.flush()

    return maturity


async def calculate_topic_maturity(topic_id: UUID, db: AsyncSession) -> float:
    """
    Calculate and persist the maturity_percent of a Topic.

    Maturity = (number of Done Deliverables) / (total non-deleted Deliverables) * 100
    Returns the calculated percentage (0.0 if no deliverables exist).
    """
    from app.models.deliverable import Deliverable, DeliverableStatus
    from app.models.topic import Topic

    total_result = await db.execute(
        select(func.count(Deliverable.id)).where(
            Deliverable.topic_id == topic_id,
            Deliverable.is_deleted.is_(False),
        )
    )
    total: int = total_result.scalar_one()

    if total == 0:
        maturity = 0.0
    else:
        done_result = await db.execute(
            select(func.count(Deliverable.id)).where(
                Deliverable.topic_id == topic_id,
                Deliverable.is_deleted.is_(False),
                Deliverable.status == DeliverableStatus.done,
            )
        )
        done: int = done_result.scalar_one()
        maturity = round((done / total) * 100, 2)

    topic = await db.get(Topic, topic_id)
    if topic:
        topic.maturity_percent = maturity
        await db.flush()

    return maturity


async def recalculate_upwards(
    entity_type: str, entity_id: UUID, db: AsyncSession
) -> None:
    """
    Trigger a maturity recalculation for all ancestors of the given entity.

    Supported entity_type values: "user_story", "bug", "task"

    For a UserStory or Bug change:
        Deliverable maturity → Topic maturity

    For a Task change, we walk up to the UserStory or Bug level first, then
    follow the same path.
    """
    from app.models.task import Task
    from app.models.user_story import UserStory

    if entity_type == "task":
        task = await db.get(Task, entity_id)
        if task is None or task.is_deleted:
            return
        if task.user_story_id:
            await recalculate_upwards("user_story", task.user_story_id, db)
        elif task.bug_id:
            await recalculate_upwards("bug", task.bug_id, db)
        return

    if entity_type == "user_story":
        user_story = await db.get(UserStory, entity_id)
        if user_story is None or user_story.is_deleted:
            return

        deliverable_id = user_story.deliverable_id
        await calculate_deliverable_maturity(deliverable_id, db)

        from app.models.deliverable import Deliverable

        deliverable = await db.get(Deliverable, deliverable_id)
        if deliverable and not deliverable.is_deleted and deliverable.topic_id:
            await calculate_topic_maturity(deliverable.topic_id, db)
        return

    if entity_type == "bug":
        from app.models.bug import Bug

        bug = await db.get(Bug, entity_id)
        if bug is None or bug.is_deleted:
            return

        deliverable_id = bug.deliverable_id
        await calculate_deliverable_maturity(deliverable_id, db)

        from app.models.deliverable import Deliverable

        deliverable = await db.get(Deliverable, deliverable_id)
        if deliverable and not deliverable.is_deleted and deliverable.topic_id:
            await calculate_topic_maturity(deliverable.topic_id, db)
