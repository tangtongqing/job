"""事件服务测试：待办查询语义 + 事务回滚。

对照返工任务 §6.6/6.7。
"""

import datetime

from src.db.models import ApplicationEvent
import src.core.events as ev


def test_future_todo_queryable(session, application_id):
    """创建未来 scheduled_at 事件后，get_upcoming_todos 能查到。"""
    future = datetime.datetime.utcnow() + datetime.timedelta(days=3)
    with session.begin_nested():
        ev.add_test(session, application_id, scheduled_at=future)

    todos = ev.get_upcoming_todos(session, days=7)
    assert len(todos) == 1
    assert todos[0].scheduled_at == future
    assert todos[0].occurred_at is None  # 未发生


def test_occurred_excluded_from_todo(session, application_id):
    """设置 occurred_at 后，不再出现在待办中。"""
    future = datetime.datetime.utcnow() + datetime.timedelta(days=3)
    with session.begin_nested():
        ev.add_interview(session, application_id, scheduled_at=future)

    # 还未发生 → 应在待办
    assert len(ev.get_upcoming_todos(session, days=7)) == 1

    # 标记为已发生
    with session.begin_nested():
        evt = session.query(ApplicationEvent).filter_by(
            event_type="interview"
        ).first()
        evt.occurred_at = datetime.datetime.utcnow()

    # 已发生 → 不在待办
    assert len(ev.get_upcoming_todos(session, days=7)) == 0


def test_event_service_no_internal_commit(session, application_id):
    """事件服务不内部 commit，外层 rollback 后不落库。"""
    # 用独立连接验证，避免 fixture session 干扰
    from sqlalchemy.orm import Session as SessionDirect

    # add 后直接 rollback，事件不应落库
    s2 = SessionDirect(bind=session.bind)
    s2.begin()
    ev.add_note(s2, application_id, "测试备注")
    s2.rollback()
    s2.close()

    # 重新查，不应有 note 事件
    count = session.query(ApplicationEvent).filter_by(
        application_id=application_id, event_type="note"
    ).count()
    assert count == 0, "外层 rollback 后事件不应落库"
