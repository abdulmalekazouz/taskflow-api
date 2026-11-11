"""Project creation, listing, and membership management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from taskflow.database import get_db
from taskflow.dependencies import get_current_user, get_project_membership, require_project_owner
from taskflow.models.membership import MEMBER_ROLE, OWNER_ROLE, ProjectMembership
from taskflow.models.project import Project
from taskflow.models.user import User
from taskflow.schemas.project import MemberAdd, MemberRead, ProjectCreate, ProjectRead

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Creates a project, making the caller its owner and first member.

    Args:
        payload: The requested name/description.
        current_user: The authenticated user, who becomes the owner.
        db: The request-scoped database session.

    Returns:
        The newly created project.
    """
    project = Project(name=payload.name, description=payload.description, owner_id=current_user.id)
    db.add(project)
    await db.flush()

    db.add(ProjectMembership(project_id=project.id, user_id=current_user.id, role=OWNER_ROLE))
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead])
async def list_my_projects(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[Project]:
    """Lists every project the current user is a member of.

    Args:
        current_user: The authenticated user.
        db: The request-scoped database session.

    Returns:
        The user's projects, in no particular order.
    """
    result = await db.execute(
        select(Project)
        .join(ProjectMembership, ProjectMembership.project_id == Project.id)
        .where(ProjectMembership.user_id == current_user.id)
    )
    return list(result.scalars().all())


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _membership: ProjectMembership = Depends(get_project_membership),
) -> Project:
    """Fetches one project, if the caller is a member.

    Args:
        project_id: The project to fetch.
        db: The request-scoped database session.
        _membership: Enforces that the caller is a project member;
            unused beyond that check (hence the leading underscore).

    Returns:
        The project.
    """
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("/{project_id}/members", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
async def add_member(
    project_id: int,
    payload: MemberAdd,
    db: AsyncSession = Depends(get_db),
    _owner_membership: ProjectMembership = Depends(require_project_owner),
) -> ProjectMembership:
    """Adds a user to a project as a member (owner-only).

    Args:
        project_id: The project to add a member to.
        payload: The email of the user to add.
        db: The request-scoped database session.
        _owner_membership: Enforces that the caller owns the project;
            unused beyond that check.

    Returns:
        The newly created membership.

    Raises:
        HTTPException: 404 if no user has that email; 400 if they are
            already a member.
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user with that email")

    existing = await db.execute(
        select(ProjectMembership).where(
            ProjectMembership.project_id == project_id, ProjectMembership.user_id == user.id
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member"
        )

    membership = ProjectMembership(project_id=project_id, user_id=user.id, role=MEMBER_ROLE)
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership


@router.get("/{project_id}/members", response_model=list[MemberRead])
async def list_members(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    _membership: ProjectMembership = Depends(get_project_membership),
) -> list[ProjectMembership]:
    """Lists every member of a project.

    Args:
        project_id: The project to list members for.
        db: The request-scoped database session.
        _membership: Enforces that the caller is a project member;
            unused beyond that check.

    Returns:
        The project's memberships.
    """
    result = await db.execute(
        select(ProjectMembership).where(ProjectMembership.project_id == project_id)
    )
    return list(result.scalars().all())
