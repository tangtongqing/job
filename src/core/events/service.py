"""事件服务（database-schema.md §3.4 + system-architecture.md §4.2）。

负责写入非状态变更的事件（面试/笔试/材料/offer/note）。
状态变更事件由状态机引擎写入，这里只处理"附加事件"。

事务边界（返工修正）：
- 服务函数只 session.add() / flush()，不内部 commit()
- 由上层（API handler / use case）统一提交或回滚
- 这样可以把"状态流转 + 事件补充"放进同一事务

待办语义（返工修正）：
- 面试/笔试/材料事件：scheduled_at=计划时间，occurred_at=完成时间
- 传入 scheduled_at 但未传 occurred_at → 创建未来待办（occurred_at=None）
- 传入 occurred_at → 记录已发生事件
- 都不传 → 默认记录为已发生（occurred_at=now），表示即时事件
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.db.models import (
    ApplicationEvent,
    Application,
    EVT_INTERVIEW,
    EVT_TEST,
    EVT_MATERIAL_SUBMIT,
    EVT_OFFER,
    EVT_NOTE,
)


# ---------- 写入：不内部 commit，由上层提交 ----------


def add_interview(
    session: Session,
    application_id: int,
    round: int | None = None,
    scheduled_at: datetime | None = None,
    occurred_at: datetime | None = None,
    note: str | None = None,
) -> ApplicationEvent:
    """记录面试事件（可多轮，round 表示轮次）。

    - 传 scheduled_at 未传 occurred_at：创建未来待办（occurred_at=None）
    - 传 occurred_at：记录已发生
    - 都不传：默认记录为已发生
    """
    actual_occurred = occurred_at
    if scheduled_at is None and occurred_at is None:
        actual_occurred = datetime.utcnow()

    event = ApplicationEvent(
        application_id=application_id,
        event_type=EVT_INTERVIEW,
        round=round,
        scheduled_at=scheduled_at,
        occurred_at=actual_occurred,
        is_correction=False,
        note=note,
    )
    session.add(event)
    session.flush()
    return event


def add_test(
    session: Session,
    application_id: int,
    scheduled_at: datetime | None = None,
    occurred_at: datetime | None = None,
    note: str | None = None,
) -> ApplicationEvent:
    """记录笔试/测评事件。待办语义同 add_interview。"""
    actual_occurred = occurred_at
    if scheduled_at is None and occurred_at is None:
        actual_occurred = datetime.utcnow()

    event = ApplicationEvent(
        application_id=application_id,
        event_type=EVT_TEST,
        scheduled_at=scheduled_at,
        occurred_at=actual_occurred,
        is_correction=False,
        note=note,
    )
    session.add(event)
    session.flush()
    return event


def add_material_submit(
    session: Session,
    application_id: int,
    scheduled_at: datetime | None = None,
    occurred_at: datetime | None = None,
    note: str | None = None,
) -> ApplicationEvent:
    """记录材料提交事件。待办语义同 add_interview。"""
    actual_occurred = occurred_at
    if scheduled_at is None and occurred_at is None:
        actual_occurred = datetime.utcnow()

    event = ApplicationEvent(
        application_id=application_id,
        event_type=EVT_MATERIAL_SUBMIT,
        scheduled_at=scheduled_at,
        occurred_at=actual_occurred,
        is_correction=False,
        note=note,
    )
    session.add(event)
    session.flush()
    return event


def add_offer(
    session: Session,
    application_id: int,
    occurred_at: datetime | None = None,
    note: str | None = None,
) -> ApplicationEvent:
    """记录 Offer 事件（总是已发生）。"""
    event = ApplicationEvent(
        application_id=application_id,
        event_type=EVT_OFFER,
        occurred_at=occurred_at or datetime.utcnow(),
        is_correction=False,
        note=note,
    )
    session.add(event)
    session.flush()
    return event


def add_note(
    session: Session,
    application_id: int,
    content: str,
) -> ApplicationEvent:
    """记录备注事件（总是已发生）。"""
    event = ApplicationEvent(
        application_id=application_id,
        event_type=EVT_NOTE,
        occurred_at=datetime.utcnow(),
        is_correction=False,
        note=content,
    )
    session.add(event)
    session.flush()
    return event


# ---------- 查询：待办（未来 N 天的面试/笔试/材料，未发生）----------


def get_upcoming_todos(
    session: Session,
    days: int = 7,
    now: datetime | None = None,
) -> list[ApplicationEvent]:
    """获取未来 N 天的待办事件。

    查询条件：scheduled_at 非空 AND occurred_at 为空 AND scheduled_at 在未来 N 天。
    对应 database-schema §4.4 待办查询，用 idx_event_todo 索引。
    """
    now = now or datetime.utcnow()
    end = now + timedelta(days=days)

    return (
        session.query(ApplicationEvent)
        .filter(
            ApplicationEvent.event_type.in_(
                [EVT_INTERVIEW, EVT_TEST, EVT_MATERIAL_SUBMIT]
            ),
            ApplicationEvent.scheduled_at.isnot(None),
            ApplicationEvent.occurred_at.is_(None),
            ApplicationEvent.scheduled_at >= now,
            ApplicationEvent.scheduled_at <= end,
        )
        .order_by(ApplicationEvent.scheduled_at.asc())
        .all()
    )


# ---------- 查询：漏斗 ----------


def get_funnel(session: Session) -> dict[str, int]:
    """获取投递漏斗数据（各状态去重计数，排除纠错）。"""
    from sqlalchemy import func

    rows = (
        session.query(
            ApplicationEvent.to_status,
            func.count(ApplicationEvent.application_id.distinct()),
        )
        .filter(
            ApplicationEvent.event_type == "status_change",
            ApplicationEvent.is_correction.is_(False),
        )
        .group_by(ApplicationEvent.to_status)
        .all()
    )
    return {status: count for status, count in rows}
