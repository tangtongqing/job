"""AI 解析结果 Schema。

对应 TASK-BE-AI-001 §2。
置信度归一到 [0,1]。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator


# 解析可建议的状态子集（非终态 + rejected）
SUGGESTABLE_STATUSES = frozenset(
    {"applied", "test", "interviewing", "offer_pending", "rejected"}
)


class ParsedEmailResult(BaseModel):
    """邮件解析结果（三级降级统一输出）。"""

    parsed: bool = False
    company: str | None = None
    title: str | None = None
    suggested_status: str | None = None
    interview_time: datetime | None = None
    confidence: float = 0.0
    degraded: bool = False
    matched_application_id: int | None = None
    reasoning: str | None = None

    @field_validator("confidence")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        """置信度归一到 [0, 1]。"""
        if v < 0:
            return 0.0
        if v > 1:
            return 1.0
        return v

    @field_validator("suggested_status")
    @classmethod
    def _validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if v not in SUGGESTABLE_STATUSES:
            return None  # 非法状态 → 置空，触发上层降级
        return v
