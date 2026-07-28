"""投递管理路由（api-contract.md 模块 C）。

返工002 修正：
- batch-transition 契约字段（succeeded/failed/total/计数）+ 每条独立事务
- create application 写初始 applied 事件
- application 详情含 events 时间线
- transition 响应含本次 event
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.models import (
    Application,
    ApplicationEvent,
    Job,
    UserJobAction,
    ACTION_TO_APPLY,
    APP_APPLIED,
    TERMINAL_STATUSES,
    EVT_STATUS_CHANGE,
)
from src.schemas.models import (
    ApplicationOut,
    ApplicationCreate,
    ManualApplicationCreate,
    ApplicationEventOut,
    TransitionRequest,
    BatchTransitionRequest,
)
from src.api.responses import (
    make_paginated,
    make_success,
    NotFoundError,
    InvalidTransitionError,
    ConflictError,
    ValidationError,
)
from src.core import statemachine as sm
from src.core.events import add_interview, add_test
from src.core.statemachine import get_history

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("")
def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    job_id: int | None = None,
    db: Session = Depends(get_db),
):
    """投递列表，支持按状态/岗位筛选。

    QA-REWORK-002：返回时 join Job 摘要（company/title），避免前端 N+1 请求。
    """
    q = select(Application)
    if status:
        q = q.where(Application.status == status)
    if job_id:
        q = q.where(Application.job_id == job_id)

    total = db.scalar(select(func.count()).select_from(q.subquery()))
    q = q.order_by(Application.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    apps = db.scalars(q).all()

    # 批量预加载关联 Job（一次查询，避免 N+1）
    job_ids = {a.job_id for a in apps}
    job_map: dict[int, Job] = {}
    if job_ids:
        jobs = db.scalars(select(Job).where(Job.id.in_(job_ids))).all()
        job_map = {j.id: j for j in jobs}

    # QA-REWORK-002 修复：用列表专用 schema，显式构造 dict 避免 events 懒加载 N+1
    result = []
    for a in apps:
        job = job_map.get(a.job_id)
        result.append({
            "id": a.id,
            "job_id": a.job_id,
            "status": a.status,
            "applied_at": a.applied_at.isoformat() if a.applied_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            "notes": a.notes,
            "job": {
                "id": job.id,
                "company": job.company,
                "title": job.title,
            } if job else None,
        })

    return make_paginated(result, page, page_size, total)


def _create_application_record(
    db: Session,
    job: Job,
    *,
    applied_at: datetime,
    notes: str | None,
) -> Application:
    """在当前事务中创建投递和初始事件，并结束待投递标记。"""
    existing = db.scalar(
        select(Application).where(
            Application.job_id == job.id,
            ~Application.status.in_(list(TERMINAL_STATUSES)),
        )
    )
    if existing:
        raise ConflictError(f"Job {job.id} 已有进行中的投递 (id={existing.id})")

    app = Application(
        job_id=job.id,
        status=APP_APPLIED,
        applied_at=applied_at,
        updated_at=applied_at,
        notes=notes,
    )
    db.add(app)
    db.flush()
    db.add(
        ApplicationEvent(
            application_id=app.id,
            event_type=EVT_STATUS_CHANGE,
            from_status=None,
            to_status=APP_APPLIED,
            occurred_at=applied_at,
            is_correction=False,
        )
    )

    pending_actions = db.scalars(
        select(UserJobAction).where(
            UserJobAction.job_id == job.id,
            UserJobAction.action_type == ACTION_TO_APPLY,
            UserJobAction.ended_at.is_(None),
        )
    ).all()
    for action in pending_actions:
        action.ended_at = applied_at
    return app


@router.post("/manual", status_code=201)
def create_manual_application(
    payload: ManualApplicationCreate,
    db: Session = Depends(get_db),
):
    """原子补录岗位库外的岗位、投递与初始时间线。"""
    job_query = select(Job).where(
        Job.source == "manual",
        Job.company == payload.company,
        Job.title == payload.title,
    )
    if payload.location is None:
        job_query = job_query.where(Job.location.is_(None))
    else:
        job_query = job_query.where(Job.location == payload.location)
    job = db.scalar(job_query)

    if job is None:
        job = Job(
            company=payload.company,
            title=payload.title,
            location=payload.location,
            apply_url=payload.source_url,
            source="manual",
            source_url=payload.source_url,
        )
        db.add(job)
        db.flush()
    elif payload.source_url:
        # 复用已结束的手动岗位时，用本次补录的来源链接更新缺失字段。
        job.source_url = payload.source_url
        job.apply_url = payload.source_url

    app = _create_application_record(
        db,
        job,
        applied_at=payload.applied_at or datetime.utcnow(),
        notes=payload.notes,
    )
    db.commit()
    db.refresh(app)
    return {"data": ApplicationOut.model_validate(app).model_dump()}


@router.post("", status_code=201)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    """创建投递记录（初始状态 applied）+ 写初始 applied 事件。"""
    job = db.get(Job, payload.job_id)
    if not job:
        raise NotFoundError(f"Job {payload.job_id} not found")

    now = datetime.utcnow()
    app = _create_application_record(
        db,
        job,
        applied_at=now,
        notes=payload.notes,
    )

    db.commit()
    db.refresh(app)
    return {"data": ApplicationOut.model_validate(app).model_dump()}


@router.get("/{app_id}")
def get_application(app_id: int, db: Session = Depends(get_db)):
    """投递详情（含岗位信息 + 事件时间线）。"""
    app = db.get(Application, app_id)
    if not app:
        raise NotFoundError(f"Application {app_id} not found")

    app_dict = ApplicationOut.model_validate(app).model_dump()

    # 岗位信息
    job = db.get(Job, app.job_id)
    if job:
        from src.schemas.models import JobOut
        app_dict["job"] = JobOut.model_validate(job).model_dump()

    # 事件时间线（occurred_at ASC）
    events = get_history(db, app_id)
    app_dict["events"] = [ApplicationEventOut.model_validate(e).model_dump() for e in events]

    return {"data": app_dict}


@router.post("/{app_id}/transition")
def transition_application(
    app_id: int, payload: TransitionRequest, db: Session = Depends(get_db)
):
    """状态流转 ⭐ 核心端点。响应含本次变更事件。"""
    app = db.get(Application, app_id)
    if not app:
        raise NotFoundError(f"Application {app_id} not found")

    # to_status 枚举校验已在 schema 层完成（Literal）
    try:
        app = sm.transition(
            db,
            app_id,
            payload.to_status,
            note=payload.note,
            is_correction=payload.is_correction,
            correction_reason=payload.correction_reason,
        )
    except sm.ApplicationNotFoundError:
        raise NotFoundError(f"Application {app_id} not found")
    except sm.InvalidTransitionError as e:
        raise InvalidTransitionError(
            str(e),
            details={"from_status": app.status, "to_status": payload.to_status},
        )
    except sm.CorrectionValidationError as e:
        raise ValidationError(str(e))

    # Session 关闭 autoflush，先 flush 才能准确读取本次状态事件；仍未提交。
    db.flush()

    # 查本次写入的事件（最新一条 status_change 或 correction）
    latest_event = db.scalars(
        select(ApplicationEvent)
        .where(
            ApplicationEvent.application_id == app_id,
            ApplicationEvent.event_type.in_(["status_change", "correction"]),
        )
        .order_by(ApplicationEvent.id.desc())
        .limit(1)
    ).first()

    scheduled_event = None
    if payload.scheduled_at and payload.scheduled_event_type == "interview":
        scheduled_event = add_interview(
            db,
            app_id,
            round=payload.round,
            scheduled_at=payload.scheduled_at,
            note=payload.note,
        )
    elif payload.scheduled_at and payload.scheduled_event_type == "test":
        scheduled_event = add_test(
            db,
            app_id,
            scheduled_at=payload.scheduled_at,
            note=payload.note,
        )

    # 状态事件与计划事件在同一事务中提交。
    db.commit()
    db.refresh(app)
    if latest_event:
        db.refresh(latest_event)
    if scheduled_event:
        db.refresh(scheduled_event)

    return {
        "data": {
            "application": ApplicationOut.model_validate(app).model_dump(),
            "event": ApplicationEventOut.model_validate(latest_event).model_dump() if latest_event else None,
            "scheduled_event": (
                ApplicationEventOut.model_validate(scheduled_event).model_dump()
                if scheduled_event
                else None
            ),
        }
    }


@router.post("/batch-transition")
def batch_transition(payload: BatchTransitionRequest, db: Session = Depends(get_db)):
    """批量状态流转。每条独立事务，部分失败不中断。"""
    succeeded = []
    failed = []

    for app_id in payload.application_ids:
        app = db.get(Application, app_id)
        if not app:
            failed.append({
                "application_id": app_id,
                "error_code": "NOT_FOUND",
                "message": f"Application {app_id} not found",
            })
            continue

        # 每条独立事务
        try:
            sm.transition(db, app_id, payload.to_status, note=payload.note)
            db.commit()
            succeeded.append(app_id)
        except sm.InvalidTransitionError as e:
            db.rollback()
            failed.append({
                "application_id": app_id,
                "error_code": "INVALID_TRANSITION",
                "message": str(e),
            })
        except Exception as e:
            db.rollback()
            failed.append({
                "application_id": app_id,
                "error_code": "INTERNAL_ERROR",
                "message": str(e),
            })

    return {
        "data": {
            "succeeded": succeeded,
            "failed": failed,
            "total": len(payload.application_ids),
            "success_count": len(succeeded),
            "fail_count": len(failed),
        }
    }


@router.get("/{app_id}/events")
def get_events(app_id: int, db: Session = Depends(get_db)):
    """事件时间线。"""
    app = db.get(Application, app_id)
    if not app:
        raise NotFoundError(f"Application {app_id} not found")

    events = get_history(db, app_id)
    return make_success([ApplicationEventOut.model_validate(e).model_dump() for e in events])


# ---------- AI 邮件解析（F-C.5）----------

from src.core.ai import AIParser, ApplicationMatcher
from src.core.ai.schemas import ParsedEmailResult
from pydantic import BaseModel, Field

_email_max_length = 10000


class ParseEmailRequest(BaseModel):
    email_text: str = Field(..., min_length=1, max_length=_email_max_length)


# 测试注入：覆盖默认 parser
_parser_override: AIParser | None = None


def set_ai_parser_for_testing(parser: AIParser | None) -> None:
    global _parser_override
    _parser_override = parser


def _get_parser() -> AIParser:
    return _parser_override or AIParser()


@router.post("/parse-email")
async def parse_email(payload: ParseEmailRequest, db: Session = Depends(get_db)):
    """AI 邮件解析（F-C.5）。

    只返回建议，不自动流转状态，不写 ApplicationEvent。
    """
    parser = _get_parser()
    result: ParsedEmailResult = await parser.parse_email(payload.email_text)

    # 匹配投递（只读，不写库）
    matcher = ApplicationMatcher()
    matched_id = matcher.match(db, result.company, result.title) if result.parsed else None

    return {"data": {
        "parsed": result.parsed,
        "company": result.company,
        "title": result.title,
        "suggested_status": result.suggested_status,
        "interview_time": result.interview_time,
        "confidence": result.confidence,
        "degraded": result.degraded,
        "matched_application_id": matched_id,
        "reasoning": result.reasoning,
    }}
