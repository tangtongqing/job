"""状态机引擎（database-schema.md §4.3）。

核心：状态流转的领域写入。
- 读取 + 校验 + 写入使用调用方提供的同一 Session
- Application.status 更新 + ApplicationEvent 写入由用例层原子提交
- SQLite 用应用层校验代替悲观锁（SQLite 不支持 SELECT FOR UPDATE）
"""

from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models import (
    Application,
    ApplicationEvent,
    EVT_STATUS_CHANGE,
    EVT_CORRECTION,
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
    """写入状态流转，事务提交或回滚由调用方负责。

    database-schema §4.3 v2 关键：状态与事件使用同一 Session，调用方可以
    继续附加计划事件后一次提交，任何一步失败时整体回滚。

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
    event_type = EVT_CORRECTION if is_correction else EVT_STATUS_CHANGE

    # 1. 读取当前状态。SQLite 不支持 SELECT FOR UPDATE，由应用层校验约束流转。
    app = session.get(Application, application_id)
    if app is None:
        raise ApplicationNotFoundError(application_id)
    from_status = app.status

    # 2. 应用层校验
    if is_correction:
        if not correction_reason:
            raise CorrectionValidationError("纠错必须填写原因")
        # 纠错允许任意流转（包括终态回流），不校验 TRANSITIONS
    elif not is_valid_transition(from_status, to_status):
        raise InvalidTransitionError(from_status, to_status)

    # 3. 更新 Application
    now = datetime.utcnow()
    app.status = to_status
    app.updated_at = now

    # 4. 写入 ApplicationEvent。这里不 commit，便于用例层附加事件后统一提交。
    session.add(
        ApplicationEvent(
            application_id=application_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            occurred_at=now,
            is_correction=is_correction,
            correction_reason=correction_reason,
            note=note,
        )
    )

    return app


def get_history(session: Session, application_id: int) -> list[ApplicationEvent]:
    """获取投递的完整事件历史（按时间排序）。"""
    return (
        session.query(ApplicationEvent)
        .filter(ApplicationEvent.application_id == application_id)
        .order_by(ApplicationEvent.occurred_at.asc())
        .all()
    )
