"""收藏与待投递列表。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.responses import make_paginated
from src.db.models import Job, UserJobAction, ACTION_FAVORITED, ACTION_TO_APPLY
from src.db.session import get_db
from src.schemas.models import JobOut

router = APIRouter(prefix="/user", tags=["saved-jobs"])


def _list_actions(action_type: str, page: int, page_size: int, db: Session):
    base = (
        select(UserJobAction, Job)
        .join(Job, Job.id == UserJobAction.job_id)
        .where(
            UserJobAction.action_type == action_type,
            UserJobAction.ended_at.is_(None),
        )
    )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.execute(
        base.order_by(UserJobAction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = [
        {
            "id": action.id,
            "job_id": action.job_id,
            "action_type": action.action_type,
            "job": JobOut.model_validate(job).model_dump(),
            "created_at": action.created_at,
        }
        for action, job in rows
    ]
    return make_paginated(items, page, page_size, total)


@router.get("/favorites")
def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return _list_actions(ACTION_FAVORITED, page, page_size, db)


@router.get("/to-apply")
def list_to_apply(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return _list_actions(ACTION_TO_APPLY, page, page_size, db)
