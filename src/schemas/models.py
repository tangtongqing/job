"""Pydantic schemas：请求/响应模型。

对应 api-contract.md 各端点的响应 Schema。
ORM 模型 → schema 用 from_attributes=True 转换。
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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


# ---------- Saved jobs ----------


class UserJobActionOut(ORMBase):
    id: int
    job_id: int
    action_type: Literal["favorited", "to_apply"]
    created_at: datetime


class SavedJobOut(BaseModel):
    id: int
    job_id: int
    action_type: Literal["favorited", "to_apply"]
    job: JobOut
    created_at: datetime


# ---------- Subscription ----------


class SubscriptionPayload(BaseModel):
    keyword: str | None = None
    company: str | None = None
    location: str | None = None

    @field_validator("keyword", "company", "location", mode="before")
    @classmethod
    def normalize_optional_text(cls, value):
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @model_validator(mode="after")
    def require_at_least_one_filter(self):
        if not any((self.keyword, self.company, self.location)):
            raise ValueError("订阅至少需要一个关键词、公司或地点条件")
        return self


class SubscriptionOut(ORMBase):
    id: int
    keyword: str | None = None
    company: str | None = None
    location: str | None = None
    created_at: datetime


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


class ManualApplicationCreate(BaseModel):
    """岗位库外投递的最小补录契约。"""

    company: str = Field(..., min_length=1, max_length=200)
    title: str = Field(..., min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    source_url: str | None = Field(default=None, max_length=2000)
    applied_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=5000)

    @field_validator("company", "title", "location", "source_url", "notes", mode="before")
    @classmethod
    def normalize_text(cls, value):
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str | None) -> str | None:
        if value is not None and not value.lower().startswith(("http://", "https://")):
            raise ValueError("原始链接必须以 http:// 或 https:// 开头")
        return value


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
    scheduled_at: datetime | None = None
    scheduled_event_type: Literal["interview", "test"] | None = None
    round: int | None = Field(default=None, ge=1, le=20)

    @model_validator(mode="after")
    def validate_scheduled_event(self):
        has_time = self.scheduled_at is not None
        has_type = self.scheduled_event_type is not None
        if has_time != has_type:
            raise ValueError("计划时间与计划事件类型必须同时提供")
        if not has_time:
            if self.round is not None:
                raise ValueError("面试轮次必须与计划事件同时提供")
            return self

        expected_type = {
            "interviewing": "interview",
            "test": "test",
        }.get(self.to_status)
        if expected_type != self.scheduled_event_type:
            raise ValueError("计划事件类型必须与目标状态一致")
        if self.scheduled_event_type != "interview" and self.round is not None:
            raise ValueError("只有面试计划可以设置轮次")
        if self.is_correction:
            raise ValueError("纠错流转不能同时创建计划事件")
        return self


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
