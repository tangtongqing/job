"""状态机测试：合法流转 / 非法流转 / 纠错。

对照 api-contract.md §四 + 返工任务 §6.1/6.2/6.3。
"""

import pytest
from sqlalchemy.exc import IntegrityError

from src.db.models import (
    APP_APPLIED,
    APP_TEST,
    APP_INTERVIEWING,
    APP_OFFER_PENDING,
    APP_OFFER_ACCEPTED,
    APP_OFFER_DECLINED,
    APP_REJECTED,
    APP_NO_RESPONSE,
    APP_WITHDRAWN,
    ApplicationEvent,
    EVT_CORRECTION,
)
from src.core.statemachine import (
    transition,
    is_valid_transition,
    InvalidTransitionError,
    CorrectionValidationError,
)


# ---------- 1. 合法流转 ----------


@pytest.mark.parametrize(
    "from_status,to_status",
    [
        (APP_APPLIED, APP_OFFER_PENDING),        # applied→offer_pending（返工新增）
        (APP_TEST, APP_OFFER_PENDING),           # test→offer_pending（返工新增）
        (APP_INTERVIEWING, APP_INTERVIEWING),    # 多轮自环（返工新增）
        (APP_OFFER_PENDING, APP_REJECTED),       # offer_pending→rejected（返工新增）
        (APP_OFFER_PENDING, APP_NO_RESPONSE),    # offer_pending→no_response（返工新增）
        (APP_APPLIED, APP_TEST),
        (APP_APPLIED, APP_WITHDRAWN),
        (APP_OFFER_PENDING, APP_OFFER_ACCEPTED),
    ],
)
def test_valid_transition_rules(from_status, to_status):
    """合法流转规则：直接查 TRANSITIONS。"""
    assert is_valid_transition(from_status, to_status), (
        f"{from_status}→{to_status} 应该合法"
    )


def test_transition_persists_event(session, application_id):
    """流转成功后应写入 status_change 事件。"""
    transition(session, application_id, APP_TEST)
    session.commit()

    events = session.query(ApplicationEvent).filter_by(
        application_id=application_id
    ).all()
    assert len(events) == 1
    assert events[0].to_status == APP_TEST
    assert events[0].from_status == APP_APPLIED
    assert events[0].is_correction is False


# ---------- 2. 非法流转 ----------


def test_interviewing_to_test_rejected():
    """interviewing→test 是回退流转，必须被拒（返工修正）。"""
    assert not is_valid_transition(APP_INTERVIEWING, APP_TEST), (
        "interviewing→test 是回退，应该非法"
    )


def test_interviewing_to_interviewing_allowed():
    """interviewing→interviewing 多轮面试应该合法。"""
    assert is_valid_transition(APP_INTERVIEWING, APP_INTERVIEWING)


@pytest.mark.parametrize("terminal", [
    APP_OFFER_ACCEPTED, APP_OFFER_DECLINED, APP_REJECTED, APP_NO_RESPONSE, APP_WITHDRAWN,
])
def test_terminal_normal_transition_rejected(session, application_id, terminal):
    """终态常规流转必须被拒。"""
    # 先转到终态
    if terminal == APP_OFFER_ACCEPTED:
        transition(session, application_id, APP_OFFER_PENDING)
        transition(session, application_id, APP_OFFER_ACCEPTED)
    elif terminal == APP_WITHDRAWN:
        transition(session, application_id, APP_WITHDRAWN)

    # 终态→任意 非纠错 应被拒（直接验规则）
    assert not is_valid_transition(APP_OFFER_ACCEPTED, APP_INTERVIEWING)
    assert not is_valid_transition(APP_WITHDRAWN, APP_APPLIED)


# ---------- 3. 纠错 ----------


def test_correction_without_reason_rejected(session, application_id):
    """终态纠错无原因必须抛 CorrectionValidationError。"""
    transition(session, application_id, APP_OFFER_PENDING)
    transition(session, application_id, APP_OFFER_ACCEPTED)

    with pytest.raises(CorrectionValidationError):
        transition(
            session, application_id, APP_INTERVIEWING,
            is_correction=True, correction_reason=None,
        )


def test_correction_with_reason_succeeds(session, application_id):
    """终态带原因纠错成功，写 correction 事件。"""
    transition(session, application_id, APP_OFFER_PENDING)
    transition(session, application_id, APP_OFFER_ACCEPTED)

    transition(
        session, application_id, APP_INTERVIEWING,
        is_correction=True, correction_reason="公司重新发起了面试",
    )
    session.commit()

    correction_events = session.query(ApplicationEvent).filter_by(
        application_id=application_id, event_type=EVT_CORRECTION, is_correction=True
    ).all()
    assert len(correction_events) == 1
    assert correction_events[0].correction_reason == "公司重新发起了面试"
