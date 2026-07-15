"""状态机模块导出。"""

from src.core.statemachine.transitions import is_valid_transition, TRANSITIONS
from src.core.statemachine.engine import (
    transition,
    get_history,
    StateMachineError,
    ApplicationNotFoundError,
    InvalidTransitionError,
    CorrectionValidationError,
)

__all__ = [
    "is_valid_transition",
    "TRANSITIONS",
    "transition",
    "get_history",
    "StateMachineError",
    "ApplicationNotFoundError",
    "InvalidTransitionError",
    "CorrectionValidationError",
]
