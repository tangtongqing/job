"""状态机引擎（database-schema.md §4.3）。

核心：状态流转的事务实现。
- 读取 + 校验 + 写入在同一事务（database-schema v2 关键修正）
- Application.status 更新 + ApplicationEvent 写入原子提交
- SQLite 用应用层校验代替悲观锁（SQLite 不支持 SELECT FOR UPDATE）
"""

from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models import (
    Application,
    ApplicationEvent,
    EVT_STATUS_CHANGE,
    EVT_CORRECTION,
    is_terminal,
)
from src.core.statemachine.transitions import is_valid_transition


class StateMachineError(Exception):
    """状态机错误基类。"""


class ApplicationNotFoundError(StateMachineError):
    def __init__(self, application_id: int):
        super().__init__(f"Application {application_id} not found")


class InvalidTransitionError(StateMachineError):
    def __init__(self, from_status: str, to_status: str):
        super().__init__(f"不允许从 {from_status} 流转到 {to_status}")


class CorrectionValidationError(StateMachineError):
    def __init__(self, reason: str):
        super().__init__(reason)


def transition(
    session: Session,
    application_id: int,
    to_status: str,
    note: str | None = None,
    is_correction: bool = False,
    correction_reason: str | None = None,
) -> Application:
    """状态流转（原子操作）。

    database-schema §4.3 v2 关键：读取 + 校验 + 写入在同一事务内。

    Args:
        session: SQLAlchemy Session
        application_id: 投递记录 id
        to_status: 目标状态（英文 code）
        note: 可选备注
        is_correction: 是否纠错（终态回流必须为 True）
        correction_reason: 纠错原因（is_correction=True 时必填）

    Returns:
        更新后的 Application

    Raises:
        ApplicationNotFoundError / InvalidTransitionError / CorrectionValidationError
    """
    app = None
    event_type = EVT_CORRECTION if is_correction else EVT_STATUS_CHANGE

    # v2 关键：整个流程在事务内
    with session.begin_nested() if session.in_transaction() else session.begin():
        # 1. 读取当前状态（事务内，SQLite 数据库级锁保证一致性）
        app = session.query(Application).get(application_id)
        if app is None:
            raise ApplicationNotFoundError(application_id)
        from_status = app.status

        # 2. 应用层校验
        if is_correction:
            if not correction_reason:
                raise CorrectionValidationError("纠错必须填写原因")
            # 纠错允许任意流转（包括终态回流），不校验 TRANSITIONS
        else:
            if not is_valid_transition(from_status, to_status):
                raise InvalidTransitionError(from_status, to_status)

        # 3. 更新 Application
        now = datetime.utcnow()
        app.status = to_status
        app.updated_at = now

        # 4. 写入 ApplicationEvent（同一事务，原子提交）
        event = ApplicationEvent(
            application_id=application_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            occurred_at=now,
            is_correction=is_correction,
            correction_reason=correction_reason,
            note=note,
        )
        session.add(event)

    return app


def get_history(session: Session, application_id: int) -> list[ApplicationEvent]:
    """获取投递的完整事件历史（按时间排序）。"""
    return (
        session.query(ApplicationEvent)
        .filter(ApplicationEvent.application_id == application_id)
        .order_by(ApplicationEvent.occurred_at.asc())
        .all()
    )
