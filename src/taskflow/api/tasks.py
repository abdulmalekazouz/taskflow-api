"""Task creation, listing (paginated/filterable), updating, and deletion.

Every route here is nested under a project and depends on
`get_project_membership`, so a non-member gets a 403 before any task
data is touched.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from taskflow.database import get_db, get_session_factory
from taskflow.dependencies import get_project_membership
from taskflow.models.task import Task, TaskStatus
from taskflow.notifications import notify_assignment
from taskflow.schemas.task import TaskCreate, TaskPage, TaskRead, TaskUpdate

router = APIRouter(
    prefix="/projects/{project_id}/tasks",
    tags=["tasks"],
    dependencies=[Depends(get_project_membership)],
)


async def _get_task_or_404(project_id: int, task_id: int, db: AsyncSession) -> Task:
    task = await db.get(Task, task_id)
    if task is None or task.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: int,
    payload: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> Task:
    """Creates a task within a project.

    If the task is created with an assignee, queues a background
    notification for them (see `taskflow.notifications`).

    Args:
        project_id: The owning project.
        payload: The task's title/description/assignee/due date.
        background_tasks: FastAPI's background-task queue.
        db: The request-scoped database session.
        session_factory: Used by the queued notification task, which
            runs after this request's session may already be closing.

    Returns:
        The newly created task.
    """
    task = Task(project_id=project_id, **payload.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)

    if task.assignee_id is not None:
        background_tasks.add_task(
            notify_assignment,
            session_factory,
            task.assignee_id,
            f"You were assigned to task '{task.title}'.",
        )

    return task


@router.get("", response_model=TaskPage)
async def list_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    assignee_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> TaskPage:
    """Lists a project's tasks, with optional filtering and pagination.

    Args:
        project_id: The project to list tasks for.
        db: The request-scoped database session.
        status_filter: If given, only return tasks in this status.
        assignee_id: If given, only return tasks assigned to this user.
        page: 1-indexed page number.
        page_size: Number of tasks per page (1-100).

    Returns:
        A `TaskPage` with the matching slice of tasks and the total
        count of tasks matching the filters (across all pages).
    """
    base_query = select(Task).where(Task.project_id == project_id)
    if status_filter is not None:
        base_query = base_query.where(Task.status == status_filter)
    if assignee_id is not None:
        base_query = base_query.where(Task.assignee_id == assignee_id)

    total = (
        await db.execute(select(func.count()).select_from(base_query.subquery()))
    ).scalar_one()

    paged_query = base_query.order_by(Task.id).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(paged_query)).scalars().all()

    return TaskPage(items=list(items), total=total, page=page, page_size=page_size)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(project_id: int, task_id: int, db: AsyncSession = Depends(get_db)) -> Task:
    """Fetches one task.

    Args:
        project_id: The owning project.
        task_id: The task to fetch.
        db: The request-scoped database session.

    Returns:
        The task.
    """
    return await _get_task_or_404(project_id, task_id, db)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    project_id: int,
    task_id: int,
    payload: TaskUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> Task:
    """Partially updates a task; only fields present in the body change.

    If the update sets (or changes) the assignee, queues a background
    notification for the newly assigned user.

    Args:
        project_id: The owning project.
        task_id: The task to update.
        payload: The fields to change.
        background_tasks: FastAPI's background-task queue.
        db: The request-scoped database session.
        session_factory: Used by the queued notification task, which
            runs after this request's session may already be closing.

    Returns:
        The updated task.
    """
    task = await _get_task_or_404(project_id, task_id, db)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)

    if "assignee_id" in changes and task.assignee_id is not None:
        background_tasks.add_task(
            notify_assignment,
            session_factory,
            task.assignee_id,
            f"You were assigned to task '{task.title}'.",
        )

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(project_id: int, task_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Deletes a task.

    Args:
        project_id: The owning project.
        task_id: The task to delete.
        db: The request-scoped database session.
    """
    task = await _get_task_or_404(project_id, task_id, db)
    await db.delete(task)
    await db.commit()
