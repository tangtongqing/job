"""状态流转规则。

以 docs/architecture/api-contract.md §四「状态机流转 API 详细说明」为权威来源。

核心规则：
- 进行中状态：可往后流转，也可进入终态（withdrawn/rejected/no_response）
- interviewing → interviewing：多轮面试自环（PRD F-C.1 AC）
- 禁止回退（如 interviewing → applied），求职进度不可逆
- 终态 → 任何：禁止常规流转，必须走纠错（is_correction=True）
"""

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
    TERMINAL_STATUSES,
)

# 所有进行中状态都可进入的三个终态（api-contract §四「进行中→终态」）
_ANY_TO_TERMINAL = frozenset({APP_WITHDRAWN, APP_REJECTED, APP_NO_RESPONSE})

# 进行中状态的前进流转（api-contract §四「进行中→进行中」）
# 不含终态，终态通过 _ANY_TO_TERMINAL 补全
_PROGRESS = {
    APP_APPLIED: frozenset(
        {APP_TEST, APP_INTERVIEWING, APP_OFFER_PENDING}
    ),
    APP_TEST: frozenset(
        {APP_INTERVIEWING, APP_OFFER_PENDING}
    ),
    APP_INTERVIEWING: frozenset(
        {APP_INTERVIEWING, APP_OFFER_PENDING}  # 多轮自环 + 面试通过
    ),
    APP_OFFER_PENDING: frozenset(
        {APP_OFFER_ACCEPTED, APP_OFFER_DECLINED}
    ),
}

# 终态：常规流转无出路
for _s in TERMINAL_STATUSES:
    _PROGRESS[_s] = frozenset()

# 合法的常规流转（非纠错）= 前进流转 ∪ 任意进行中→终态
# key: from_status, value: set(允许的 to_status)
TRANSITIONS: dict[str, frozenset[str]] = {
    from_status: targets | _ANY_TO_TERMINAL
    for from_status, targets in _PROGRESS.items()
    if from_status not in TERMINAL_STATUSES
}
for _s in TERMINAL_STATUSES:
    TRANSITIONS[_s] = frozenset()


def is_valid_transition(from_status: str, to_status: str) -> bool:
    """判断常规流转是否合法（不含纠错）。

    终态 → 非终态 必须走纠错流程（is_correction=True），不在这里判断。
    """
    allowed = TRANSITIONS.get(from_status, frozenset())
    return to_status in allowed
