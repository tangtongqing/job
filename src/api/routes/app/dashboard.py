"""看板路由（api-contract.md 模块 B）。

返工002 重写：四端点响应结构严格对齐契约。
"""

from datetime import datetime, timedelta, date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.models import (
    Application,
    ApplicationEvent,
    Job,
    Company,
    APP_TEST,
    APP_INTERVIEWING,
    APP_OFFER_PENDING,
    APP_APPLIED,
    APP_OFFER_ACCEPTED,
    TERMINAL_STATUSES,
    EVT_STATUS_CHANGE,
)
from src.api.responses import make_success, ValidationError

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# 漏斗顺序
_FUNNEL_ORDER = [APP_APPLIED, APP_TEST, APP_INTERVIEWING, APP_OFFER_PENDING, APP_OFFER_ACCEPTED]
# 有效进展状态（trend 用）
_PROGRESS_STATUSES = [APP_TEST, APP_INTERVIEWING, APP_OFFER_PENDING]


@router.get("/kpi")
def kpi(db: Session = Depends(get_db)):
    """KPI 卡片。"""
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())

    total_jobs = db.scalar(select(func.count(Job.id))) or 0
    today_new_jobs = db.scalar(
        select(func.count(Job.id)).where(Job.collected_at >= today_start)
    ) or 0
    total_applications = db.scalar(select(func.count(Application.id))) or 0
    pending_applications = db.scalar(
        select(func.count(Application.id)).where(~Application.status.in_(list(TERMINAL_STATUSES)))
    ) or 0

    # by_status
    rows = db.execute(
        select(Application.status, func.count(Application.id)).group_by(Application.status)
    ).all()
    by_status = {s: c for s, c in rows}

    return make_success({
        "today_new_jobs": today_new_jobs,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "pending_applications": pending_applications,
        "by_status": by_status,
    })


@router.get("/funnel")
def funnel(db: Session = Depends(get_db)):
    """投递漏斗：按状态机顺序统计各阶段累计到达数。"""
    total_applications = db.scalar(select(func.count(Application.id))) or 0

    # 用事件累计统计“到达过该阶段”的投递数，而不是当前状态分布。
    rows = db.execute(
        select(
            ApplicationEvent.to_status,
            func.count(func.distinct(ApplicationEvent.application_id)),
        )
        .where(
            and_(
                ApplicationEvent.event_type == EVT_STATUS_CHANGE,
                ApplicationEvent.is_correction.is_(False),
                ApplicationEvent.to_status.in_(_FUNNEL_ORDER),
            )
        )
        .group_by(ApplicationEvent.to_status)
    ).all()
    status_counts = {s: c for s, c in rows}

    funnel_items = []
    prev_count = None
    for status in _FUNNEL_ORDER:
        count = status_counts.get(status, 0)
        if prev_count is None:
            rate = 1.0
        elif prev_count == 0:
            rate = 0.0
        else:
            rate = round(count / prev_count, 4)
        funnel_items.append({"status": status, "count": count, "rate": rate})
        prev_count = count

    return make_success({
        "funnel": funnel_items,
        "total_applications": total_applications,
    })


@router.get("/trend")
def trend(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """有效进展趋势：近N天的 test/interviewing/offer_pending 事件数。"""
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=days - 1)
    start = datetime.combine(start_date, datetime.min.time())

    rows = db.execute(
        select(
            func.date(ApplicationEvent.occurred_at).label("d"),
            func.count(ApplicationEvent.id).label("c"),
        )
        .where(
            and_(
                ApplicationEvent.event_type == EVT_STATUS_CHANGE,
                ApplicationEvent.to_status.in_(_PROGRESS_STATUSES),
                ApplicationEvent.is_correction.is_(False),
                ApplicationEvent.occurred_at >= start,
            )
        )
        .group_by("d")
        .order_by("d")
    ).all()

    # 补齐 0 值日期
    counts_by_date = {str(r.d): r.c for r in rows}
    points = []
    total = 0
    cur = start_date
    while cur <= today:
        c = counts_by_date.get(str(cur), 0)
        points.append({"date": str(cur), "count": c})
        total += c
        cur += timedelta(days=1)

    return make_success({"trend": points, "total": total})


@router.get("/distribution")
def distribution(
    dimension: str = Query("job_category"),
    db: Session = Depends(get_db),
):
    """分布：按维度统计投递分布。"""
    valid_dims = {"job_category", "location", "company_category"}
    if dimension not in valid_dims:
        raise ValidationError(
            f"非法 dimension: {dimension}",
            details={"valid_dimensions": list(valid_dims)},
        )

    if dimension == "company_category":
        # Job.company == Company.name 关联 Company.category
        rows = db.execute(
            select(
                func.coalesce(Company.category, "未分类").label("label"),
                func.count(Application.id).label("c"),
            )
            .select_from(Application)
            .join(Job, Application.job_id == Job.id)
            .outerjoin(Company, Job.company == Company.name)
            .group_by("label")
        ).all()
    else:
        col = Job.job_category if dimension == "job_category" else Job.location
        rows = db.execute(
            select(
                func.coalesce(col, "未分类").label("label"),
                func.count(Application.id).label("c"),
            )
            .select_from(Application)
            .join(Job, Application.job_id == Job.id)
            .group_by("label")
        ).all()

    total = sum(c for _, c in rows) or 1
    items = [
        {"label": label, "count": count, "rate": round(count / total, 4)}
        for label, count in rows
    ]
    return make_success({
        "dimension": dimension,
        "distribution": items,
        "total": sum(c for _, c in rows),
    })
