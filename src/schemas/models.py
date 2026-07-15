"""Pydantic schemas：请求/响应模型。

对应 api-contract.md 各端点的响应 Schema。
ORM 模型 → schema 用 from_attributes=True 转换。
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Job ----------


class JobOut(ORMBase):
    id: int
    company: str
    title: str
    location: str | None = None
    salary: str | None = None
    jd: str | None = None
    requirement: str | None = None
    apply_url: str | None = None
    source: str
    source_url: str | None = None
    job_category: str | None = None
    graduation_year: str | None = None
    education: str | None = None
    experience: str | None = None
    collected_at: datetime | None = None
    published_at: datetime | None = None
    deadline: datetime | None = None
    last_verified_at: datetime | None = None
    is_valid: bool = True
    is_intern: bool = False
    is_fresh: bool = False
    status: str = "displaying"


class JobCreate(BaseModel):
    company: str
    title: str
    location: str | None = None
    salary: str | None = None
    jd: str | None = None
    requirement: str | None = None
    apply_url: str | None = None
    source: str = "manual"  # 手动录入默认 source
    job_category: str | None = None
    graduation_year: str | None = None
    education: str | None = None
    experience: str | None = None
    deadline: datetime | None = None
    is_intern: bool = False
    is_fresh: bool = False


# ---------- Application ----------


class JobSummary(BaseModel):
    """岗位摘要（列表返回的 job 子对象，不含全量字段）。"""

    id: int
    company: str
    title: str


class ApplicationListItem(ORMBase):
    """列表专用 schema（不含 events，避免 N+1 懒加载）。

    QA-REWORK-002 修复：列表端点用此 schema，详情端点才用 ApplicationOut。
    """

    id: int
    job_id: int
    status: str
    applied_at: datetime
    updated_at: datetime
    notes: str | None = None
    job: JobSummary | None = None
    company: str
    title: str


class ApplicationOut(ORMBase):
    id: int
    job_id: int
    status: str
    applied_at: datetime
    updated_at: datetime
    notes: str | None = None
    # 关联岗位（详情用）
    job: JobOut | None = None
    # 事件时间线（详情用）
    events: list["ApplicationEventOut"] | None = None


class TransitionResponse(BaseModel):
    """transition 端点响应：含本次变更事件。"""
    application: ApplicationOut
    event: "ApplicationEventOut"


class ApplicationCreate(BaseModel):
    job_id: int
    notes: str | None = None


# 9 状态英文 code（用于 to_status 枚举校验）
VALID_TO_STATUSES = Literal[
    "applied", "test", "interviewing", "offer_pending",
    "offer_accepted", "offer_declined", "rejected", "no_response", "withdrawn",
]


class TransitionRequest(BaseModel):
    to_status: VALID_TO_STATUSES
    note: str | None = None
    is_correction: bool = False
    correction_reason: str | None = None


class BatchTransitionRequest(BaseModel):
    application_ids: list[int]
    to_status: VALID_TO_STATUSES
    note: str | None = None


# ---------- ApplicationEvent ----------


class ApplicationEventOut(ORMBase):
    id: int
    application_id: int
    event_type: str
    from_status: str | None = None
    to_status: str | None = None
    round: int | None = None
    scheduled_at: datetime | None = None
    occurred_at: datetime | None = None
    is_correction: bool = False
    correction_reason: str | None = None
    note: str | None = None


# ---------- Dashboard ----------


class KPIOut(BaseModel):
    total_applications: int
    testing: int
    interviewing: int
    offers: int


class FunnelItem(BaseModel):
    status: str
    count: int
    rate: float  # 相对 applied 的转化率


class TrendPoint(BaseModel):
    date: str
    count: int


class DistributionItem(BaseModel):
    label: str
    count: int


# ---------- Todo ----------


class TodoJobInfo(BaseModel):
    company: str | None = None
    title: str | None = None


class TodoOut(BaseModel):
    """todo 端点 item（api-contract 模块 E）。"""
    event_id: int
    application_id: int
    event_type: str
    scheduled_at: datetime | None = None
    occurred_at: datetime | None = None
    round: int | None = None
    note: str | None = None
    job: TodoJobInfo | None = None
    days_left: int | None = None


# ---------- 通用 ----------


class IdOut(BaseModel):
    id: int


class MessageOut(BaseModel):
    message: str
