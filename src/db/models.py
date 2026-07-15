"""JobPulse ORM 模型。7 表，对应 database-schema.md v2。

关键设计决策：
- 所有枚举字段用英文 code 存储（中文由应用层映射）
- Application + ApplicationEvent 写入同一事务（状态机原子性）
- Application 部分唯一索引：同一岗位同时只能有一个非终态投递
- updated_at 用 ORM 钩子自动更新（SQLite 无原生 ON UPDATE）
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from src.db.session import Base


# ---------- 状态枚举常量（应用层使用，DB 只存英文 code）----------

# Job.status
JOB_STATUS_DISPLAYING = "displaying"
JOB_STATUS_CLOSED = "closed"

# UserJobAction.action_type
ACTION_FAVORITED = "favorited"
ACTION_TO_APPLY = "to_apply"

# Application.status - 9 状态
APP_APPLIED = "applied"
APP_TEST = "test"
APP_INTERVIEWING = "interviewing"
APP_OFFER_PENDING = "offer_pending"
APP_OFFER_ACCEPTED = "offer_accepted"
APP_OFFER_DECLINED = "offer_declined"
APP_REJECTED = "rejected"
APP_NO_RESPONSE = "no_response"
APP_WITHDRAWN = "withdrawn"

# 5 终态
TERMINAL_STATUSES = frozenset(
    {
        APP_OFFER_ACCEPTED,
        APP_OFFER_DECLINED,
        APP_REJECTED,
        APP_NO_RESPONSE,
        APP_WITHDRAWN,
    }
)

# 所有合法状态
ALL_STATUSES = frozenset(
    {
        APP_APPLIED,
        APP_TEST,
        APP_INTERVIEWING,
        APP_OFFER_PENDING,
        APP_OFFER_ACCEPTED,
        APP_OFFER_DECLINED,
        APP_REJECTED,
        APP_NO_RESPONSE,
        APP_WITHDRAWN,
    }
)

# ApplicationEvent.event_type - 7 种事件
EVT_STATUS_CHANGE = "status_change"
EVT_INTERVIEW = "interview"
EVT_TEST = "test"
EVT_MATERIAL_SUBMIT = "material_submit"
EVT_OFFER = "offer"
EVT_NOTE = "note"
EVT_CORRECTION = "correction"

# CrawlLog.status
CRAWL_SUCCESS = "success"
CRAWL_FAILED = "failed"
CRAWL_SKIPPED = "skipped"

# 状态中文映射（前端/API 用）
STATUS_LABEL_CN = {
    APP_APPLIED: "已投递",
    APP_TEST: "测评笔试",
    APP_INTERVIEWING: "面试中",
    APP_OFFER_PENDING: "Offer待决定",
    APP_OFFER_ACCEPTED: "Offer已接受",
    APP_OFFER_DECLINED: "Offer已婉拒",
    APP_REJECTED: "公司拒绝",
    APP_NO_RESPONSE: "无回应关闭",
    APP_WITHDRAWN: "主动撤回",
}


def is_terminal(status: str) -> bool:
    """判断是否终态状态。"""
    return status in TERMINAL_STATUSES


# ---------- 部分索引 WHERE 条件辅助（生成 SQLAlchemy text）----------

from sqlalchemy import text as _sa_text


def _where_not_null(column: str) -> "ColumnElement":
    """生成 `column IS NOT NULL` 条件，用于部分索引。"""
    return _sa_text(f"{column} IS NOT NULL")


def _where_col_eq_false(column: str) -> "ColumnElement":
    """生成 `column = FALSE`（SQLite）/ `column IS FALSE` 兼容写法。

    SQLite/PostgreSQL 都接受 `column = 0` 的布尔比较，
    这里用 `column = FALSE` 在两端都成立（SQLite 把 FALSE 当 0）。
    """
    return _sa_text(f"{column} = FALSE")


def _where_col_true(column: str) -> "ColumnElement":
    return _sa_text(f"{column} = TRUE")


def _where_todo_pending() -> "ColumnElement":
    """待办部分索引条件：scheduled_at 非空 且 occurred_at 为空。"""
    return _sa_text("scheduled_at IS NOT NULL AND occurred_at IS NULL")


# ---------- 模型 ----------


class Job(Base):
    """岗位表（database-schema.md §3.1）。"""

    __tablename__ = "job"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    location = Column(Text)
    salary = Column(Text)
    jd = Column(Text)
    requirement = Column(Text)
    apply_url = Column(Text)
    source = Column(Text, nullable=False)
    source_url = Column(Text)
    job_category = Column(Text)
    graduation_year = Column(Text)
    education = Column(Text)
    experience = Column(Text)
    collected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    published_at = Column(DateTime)
    deadline = Column(DateTime)
    last_verified_at = Column(DateTime)
    is_valid = Column(Boolean, nullable=False, default=True)
    is_intern = Column(Boolean, nullable=False, default=False)
    is_fresh = Column(Boolean, nullable=False, default=False)
    status = Column(Text, nullable=False, default=JOB_STATUS_DISPLAYING)

    applications = relationship("Application", back_populates="job")
    user_actions = relationship("UserJobAction", back_populates="job")

    __table_args__ = (
        # CHECK 约束（database-schema §6.1）
        CheckConstraint(
            "status IN ('displaying', 'closed')", name="chk_job_status"
        ),
        # 去重唯一索引（database-schema §3.1）
        Index(
            "idx_job_dedup",
            "source",
            "company",
            "title",
            "location",
            unique=True,
        ),
        Index("idx_job_company", "company"),
        Index("idx_job_status", "status"),
        Index("idx_job_source", "source"),
        Index("idx_job_collected_at", "collected_at"),
        # 部分索引：deadline 非空才有索引价值
        Index(
            "idx_job_deadline",
            "deadline",
            sqlite_where=_where_not_null("deadline"),
            postgresql_where=_where_not_null("deadline"),
        ),
        Index(
            "idx_job_category",
            "job_category",
            sqlite_where=_where_not_null("job_category"),
            postgresql_where=_where_not_null("job_category"),
        ),
    )


class UserJobAction(Base):
    """用户-岗位关系表（database-schema.md §3.2）。只存收藏/待投递。"""

    __tablename__ = "user_job_action"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("job.id"), nullable=False)
    action_type = Column(Text, nullable=False)  # favorited / to_apply
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime)  # 创建 Application 时设值

    job = relationship("Job", back_populates="user_actions")

    __table_args__ = (
        CheckConstraint(
            "action_type IN ('favorited', 'to_apply')", name="chk_uja_action_type"
        ),
        Index("idx_uja_job_id", "job_id"),
        Index("idx_uja_action_type", "action_type"),
        # 活跃记录（未结案）的部分索引
        Index(
            "idx_uja_active",
            "job_id",
            "action_type",
            sqlite_where=_sa_text("ended_at IS NULL"),
            postgresql_where=_sa_text("ended_at IS NULL"),
        ),
    )


def _terminal_not_in_sql():
    """生成 status NOT IN (终态) 的 SQL 条件，用于部分唯一索引。

    返回 SQLAlchemy text()，给 Index 的 sqlite_where/postgresql_where 用。
    """
    from sqlalchemy import text

    terminal_list = ",".join(f"'{s}'" for s in TERMINAL_STATUSES)
    return text(f"status NOT IN ({terminal_list})")


class Application(Base):
    """投递记录表（database-schema.md §3.3）。"""

    __tablename__ = "application"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("job.id"), nullable=False)
    status = Column(Text, nullable=False)  # 9 状态英文 code
    applied_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text)

    job = relationship("Job", back_populates="applications")
    events = relationship(
        "ApplicationEvent", back_populates="application", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # CHECK：9 状态英文 code
        CheckConstraint(
            "status IN ('applied', 'test', 'interviewing', 'offer_pending', "
            "'offer_accepted', 'offer_declined', 'rejected', 'no_response', 'withdrawn')",
            name="chk_app_status",
        ),
        Index("idx_app_job_id", "job_id"),
        Index("idx_app_status", "status"),
        Index("idx_app_applied_at", "applied_at"),
        Index("idx_app_updated_at", "updated_at"),
        # v2 关键：同一岗位同时只能有一个非终态投递（部分唯一索引）
        Index(
            "idx_app_one_active_per_job",
            "job_id",
            unique=True,
            sqlite_where=_terminal_not_in_sql(),
            postgresql_where=_terminal_not_in_sql(),
        ),
    )


class ApplicationEvent(Base):
    """投递事件表（database-schema.md §3.4）⭐ 核心。

    漏斗/待办/纠错的共同命脉。与 Application.status 变更同一事务写入。
    """

    __tablename__ = "application_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(
        Integer, ForeignKey("application.id"), nullable=False
    )
    event_type = Column(Text, nullable=False)  # 7 种事件
    from_status = Column(Text)  # 仅 status_change / correction
    to_status = Column(Text)  # 仅 status_change / correction
    round = Column(Integer)  # 仅 interview
    scheduled_at = Column(DateTime)  # DDL 计划时间
    occurred_at = Column(DateTime)  # 实际发生时间
    is_correction = Column(Boolean, nullable=False, default=False)
    correction_reason = Column(Text)
    note = Column(Text)

    application = relationship("Application", back_populates="events")

    __table_args__ = (
        # CHECK：7 种事件类型
        CheckConstraint(
            "event_type IN ('status_change', 'interview', 'test', "
            "'material_submit', 'offer', 'note', 'correction')",
            name="chk_event_type",
        ),
        # 漏斗查询索引（非纠错的部分索引）
        Index(
            "idx_event_funnel",
            "event_type",
            "to_status",
            sqlite_where=_where_col_eq_false("is_correction"),
            postgresql_where=_where_col_eq_false("is_correction"),
        ),
        # 待办查询索引（scheduled_at 非空 且 occurred_at 为空）
        Index(
            "idx_event_todo",
            "event_type",
            "scheduled_at",
            sqlite_where=_where_todo_pending(),
            postgresql_where=_where_todo_pending(),
        ),
        Index("idx_event_app_id", "application_id", "occurred_at"),
        # 纠错查询索引（is_correction=TRUE 的部分索引）
        Index(
            "idx_event_correction",
            "application_id",
            sqlite_where=_where_col_true("is_correction"),
            postgresql_where=_where_col_true("is_correction"),
        ),
    )


class Subscription(Base):
    """订阅表（database-schema.md §3.5）。"""

    __tablename__ = "subscription"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(Text)
    company = Column(Text)
    location = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "idx_sub_keyword",
            "keyword",
            sqlite_where=_where_not_null("keyword"),
            postgresql_where=_where_not_null("keyword"),
        ),
        Index(
            "idx_sub_company",
            "company",
            sqlite_where=_where_not_null("company"),
            postgresql_where=_where_not_null("company"),
        ),
    )


class Company(Base):
    """公司表（database-schema.md §3.6）。"""

    __tablename__ = "company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    industry = Column(Text)
    category = Column(Text)
    website = Column(Text)

    __table_args__ = (
        Index(
            "idx_company_category",
            "category",
            sqlite_where=_where_not_null("category"),
            postgresql_where=_where_not_null("category"),
        ),
    )


class CrawlLog(Base):
    """采集日志表（database-schema.md §3.7）。"""

    __tablename__ = "crawl_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(Text, nullable=False)
    status = Column(Text, nullable=False)  # success/failed/skipped
    count = Column(Integer, default=0)
    error = Column(Text)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime)

    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed', 'skipped')", name="chk_crawl_status"
        ),
        Index("idx_crawl_source", "source"),
        Index("idx_crawl_status", "status"),
        Index("idx_crawl_started_at", "started_at"),
    )


# ---------- updated_at 自动更新钩子（SQLite 无 ON UPDATE）----------

from sqlalchemy import event as sa_event


@sa_event.listens_for(Application, "before_update")
def _application_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
