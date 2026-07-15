"""岗位路由（api-contract.md 模块 A）。

GET    /jobs            岗位列表（筛选+分页+排序）
GET    /jobs/{id}       岗位详情
POST   /jobs            手动创建岗位（手动录入兜底）
GET    /jobs/stats      采集统计
"""

from datetime import datetime
from typing import Callable

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.models import Job, JOB_STATUS_DISPLAYING
from src.schemas.models import JobOut, JobCreate, MessageOut
from src.api.responses import make_paginated, NotFoundError

router = APIRouter(prefix="/jobs", tags=["jobs"])


_verify_fetcher_override: Callable[[str], bool] | None = None


def set_verify_fetcher_for_testing(fetcher: Callable[[str], bool] | None) -> None:
    """测试注入岗位核验 fetcher，避免端点测试触网。"""
    global _verify_fetcher_override
    _verify_fetcher_override = fetcher


@router.get("")
def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    company: str | None = None,
    location: str | None = None,
    job_category: str | None = None,
    graduation_year: str | None = None,
    education: str | None = None,
    source: str | None = None,
    status: str | None = None,
    is_intern: bool | None = None,
    is_fresh: bool | None = None,
    is_valid: bool | None = None,
    db: Session = Depends(get_db),
):
    """岗位列表，支持多条件筛选 + 分页。"""
    q = select(Job)

    # 筛选条件动态拼接
    if keyword:
        q = q.where(
            (Job.title.contains(keyword)) | (Job.company.contains(keyword)) | (Job.jd.contains(keyword))
        )
    if company:
        q = q.where(Job.company.contains(company))
    if location:
        q = q.where(Job.location.contains(location))
    if job_category:
        q = q.where(Job.job_category == job_category)
    if graduation_year:
        q = q.where(Job.graduation_year == graduation_year)
    if education:
        q = q.where(Job.education == education)
    if source:
        q = q.where(Job.source == source)
    if status:
        q = q.where(Job.status == status)
    if is_intern is not None:
        q = q.where(Job.is_intern.is_(is_intern))
    if is_fresh is not None:
        q = q.where(Job.is_fresh.is_(is_fresh))
    if is_valid is not None:
        q = q.where(Job.is_valid.is_(is_valid))

    # 默认只看展示中岗位
    if status is None:
        q = q.where(Job.status == JOB_STATUS_DISPLAYING)

    # 计总数
    total = db.scalar(select(func.count()).select_from(q.subquery()))

    # 排序 + 分页
    q = q.order_by(Job.collected_at.desc()).offset((page - 1) * page_size).limit(page_size)
    jobs = db.scalars(q).all()

    return make_paginated([JobOut.model_validate(j).model_dump() for j in jobs], page, page_size, total)


@router.get("/stats")
def job_stats(db: Session = Depends(get_db)):
    """采集统计（api-contract 契约字段：today_new/total/valid/invalid）。"""
    from datetime import datetime
    today_start = datetime.combine(datetime.utcnow().date(), datetime.min.time())

    total = db.scalar(select(func.count(Job.id))) or 0
    valid = db.scalar(select(func.count(Job.id)).where(Job.is_valid.is_(True))) or 0
    invalid = db.scalar(select(func.count(Job.id)).where(Job.is_valid.is_(False))) or 0
    today_new = db.scalar(
        select(func.count(Job.id)).where(Job.collected_at >= today_start)
    ) or 0

    # 附加 by_source（契约外的额外字段，不冲突）
    rows = db.execute(
        select(Job.source, func.count(Job.id)).group_by(Job.source)
    ).all()
    by_source = {src: cnt for src, cnt in rows}

    return {"data": {
        "today_new": today_new,
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "by_source": by_source,  # 额外字段
    }}


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    """岗位详情。"""
    job = db.get(Job, job_id)
    if not job:
        raise NotFoundError(f"Job {job_id} not found")
    return {"data": JobOut.model_validate(job).model_dump()}


@router.post("", status_code=201)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    """手动创建岗位（手动录入兜底，source 默认 manual）。"""
    job = Job(
        company=payload.company,
        title=payload.title,
        location=payload.location,
        salary=payload.salary,
        jd=payload.jd,
        requirement=payload.requirement,
        apply_url=payload.apply_url,
        source=payload.source,
        job_category=payload.job_category,
        graduation_year=payload.graduation_year,
        education=payload.education,
        experience=payload.experience,
        deadline=payload.deadline,
        is_intern=payload.is_intern,
        is_fresh=payload.is_fresh,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"data": JobOut.model_validate(job).model_dump()}


@router.post("/{job_id}/verify")
def verify_job_endpoint(job_id: int, db: Session = Depends(get_db)):
    """手动触发岗位有效性核验（api-contract 模块 A）。

    用默认 fetcher（生产 HTTP），测试可注入 fake verifier。
    """
    from src.crawler.verifier import verify_job

    job = verify_job(db, job_id, fetcher=_verify_fetcher_override)
    return {"data": JobOut.model_validate(job).model_dump()}
