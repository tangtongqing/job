"""待办路由（api-contract.md 模块 E）。

返工002 修正：响应字段对齐契约（event_id/job/days_left/round）。
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.models import Job, Application
from src.core.events import get_upcoming_todos
from src.api.responses import make_success

router = APIRouter(prefix="/todo", tags=["todo"])


@router.get("")
def list_todo(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
):
    """统一待办视图：未来 N 天的面试/笔试/材料。

    响应字段（api-contract 模块 E）：event_id/application_id/event_type/scheduled_at/round/note/job/days_left
    """
    events = get_upcoming_todos(db, days=days)
    now = datetime.utcnow()

    # 批量预加载关联岗位
    app_ids = {e.application_id for e in events}
    app_job_map: dict[int, tuple[str, str]] = {}
    if app_ids:
        rows = (
            db.query(Application, Job)
            .join(Job, Application.job_id == Job.id)
            .filter(Application.id.in_(app_ids))
            .all()
        )
        app_job_map = {a.id: (j.company, j.title) for a, j in rows}

    todos = []
    for e in events:
        company, title = app_job_map.get(e.application_id, (None, None))
        # days_left: scheduled_at 距今天数
        days_left = None
        if e.scheduled_at:
            delta = e.scheduled_at.date() - now.date()
            days_left = delta.days

        todos.append({
            "event_id": e.id,
            "application_id": e.application_id,
            "event_type": e.event_type,
            "scheduled_at": e.scheduled_at.isoformat() if e.scheduled_at else None,
            "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
            "round": e.round,
            "note": e.note,
            "job": {"company": company, "title": title},
            "days_left": days_left,
        })

    return make_success(todos)
