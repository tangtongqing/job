"""JobPulse ORM 模型：M0 投递管理 + M1 公共招聘雷达。

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
    Date,
    Boolean,
    Float,
    JSON,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    CheckConstraint,
    UniqueConstraint,
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

# M1 company recruitment radar
COMPANY_CANDIDATE = "candidate"
COMPANY_VERIFIED = "verified"
COMPANY_MONITORING = "monitoring"
COMPANY_PAUSED = "paused"
COMPANY_RETIRED = "retired"

CAMPAIGN_SEASONS = frozenset(
    {"autumn", "spring", "early", "makeup", "rolling", "unknown"}
)
RECRUITMENT_TYPES = frozenset(
    {"campus_full_time", "graduate_program", "internship", "unknown"}
)
INTERNSHIP_TYPES = frozenset(
    {"not_applicable", "summer", "daily", "winter", "unknown"}
)
CAMPAIGN_STATUSES = frozenset({"upcoming", "active", "closed", "unknown"})
POSITION_STATUSES = frozenset({"open", "closed", "unknown"})
SNAPSHOT_STATUSES = frozenset({"success", "failed"})
COMPLETENESS_STATUSES = frozenset(
    {"count_matched", "pagination_verified", "incomplete", "failed"}
)
SNAPSHOT_COMPARISON_STATUSES = frozenset(
    {"pending", "baseline", "compared", "suppressed", "failed"}
)
CHANGE_EVENT_TYPES = frozenset(
    {
        "campaign_started",
        "campaign_updated",
        "campaign_closed",
        "positions_changed",
        "position_reopened",
        "page_updated",
        "source_degraded",
        "source_recovered",
    }
)
CHANGE_COMPUTATION_STATUSES = frozenset(
    {"computed", "suppressed", "review_required"}
)

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
    """Public company identity used by the M1 recruitment radar."""

    __tablename__ = "company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_company_id = Column(
        Integer,
        ForeignKey("company.id", name="fk_company_parent"),
    )
    registry_id = Column(Text)
    name = Column(Text, nullable=False, unique=True)
    aliases = Column(
        JSON,
        nullable=False,
        default=list,
        server_default=_sa_text("'[]'"),
    )
    industry = Column(Text)
    category = Column(Text)
    ownership_type = Column(Text)
    website = Column(Text)
    status = Column(
        Text,
        nullable=False,
        default=COMPANY_CANDIDATE,
        server_default=_sa_text("'candidate'"),
    )
    first_verified_at = Column(DateTime)
    last_observed_at = Column(DateTime)
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=_sa_text("CURRENT_TIMESTAMP"),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=_sa_text("CURRENT_TIMESTAMP"),
    )

    parent_company = relationship(
        "Company",
        remote_side=[id],
        back_populates="child_companies",
    )
    child_companies = relationship("Company", back_populates="parent_company")
    recruitment_campaigns = relationship(
        "RecruitmentCampaign", back_populates="company"
    )
    observed_positions = relationship(
        "ObservedPositionRef", back_populates="company"
    )
    source_snapshots = relationship("SourceSnapshot", back_populates="company")
    change_events = relationship("CompanyChangeEvent", back_populates="company")

    __table_args__ = (
        CheckConstraint(
            "status IN ('candidate', 'verified', 'monitoring', 'paused', 'retired')",
            name="chk_company_status",
        ),
        CheckConstraint(
            "parent_company_id IS NULL OR parent_company_id <> id",
            name="chk_company_not_own_parent",
        ),
        CheckConstraint(
            "status NOT IN ('verified', 'monitoring') OR "
            "first_verified_at IS NOT NULL",
            name="chk_company_verified_timestamp",
        ),
        Index("idx_company_parent", "parent_company_id"),
        Index(
            "idx_company_registry_id",
            "registry_id",
            unique=True,
            sqlite_where=_where_not_null("registry_id"),
            postgresql_where=_where_not_null("registry_id"),
        ),
        Index(
            "idx_company_category",
            "category",
            sqlite_where=_where_not_null("category"),
            postgresql_where=_where_not_null("category"),
        ),
        Index("idx_company_status", "status"),
        Index(
            "idx_company_first_verified_at",
            "first_verified_at",
            sqlite_where=_where_not_null("first_verified_at"),
            postgresql_where=_where_not_null("first_verified_at"),
        ),
    )


class RecruitmentCampaign(Base):
    """One official recruitment campaign, separate from its position list."""

    __tablename__ = "recruitment_campaign"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    source_id = Column(Text, nullable=False)
    campaign_key = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    season = Column(Text, nullable=False, default="unknown")
    campaign_year = Column(Integer)
    recruitment_type = Column(Text, nullable=False, default="unknown")
    internship_type = Column(Text, nullable=False, default="not_applicable")
    graduation_years_status = Column(
        Text,
        nullable=False,
        default="unknown",
        server_default=_sa_text("'unknown'"),
    )
    status = Column(Text, nullable=False, default="unknown")
    start_at = Column(DateTime)
    deadline = Column(DateTime)
    official_url = Column(Text, nullable=False)
    first_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    classification_confidence = Column(Float)
    classification_evidence = Column(
        JSON,
        nullable=False,
        default=dict,
        server_default=_sa_text("'{}'"),
    )

    company = relationship("Company", back_populates="recruitment_campaigns")
    graduation_cohorts = relationship(
        "CampaignGraduationYear",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
    observed_positions = relationship(
        "ObservedPositionRef", back_populates="campaign", viewonly=True
    )
    change_events = relationship(
        "CompanyChangeEvent", back_populates="campaign", viewonly=True
    )

    @property
    def graduation_years(self) -> list[int]:
        return sorted(record.graduation_year for record in self.graduation_cohorts)

    @graduation_years.setter
    def graduation_years(self, values) -> None:
        years = sorted({int(value) for value in (values or [])})
        self.graduation_cohorts = [
            CampaignGraduationYear(graduation_year=year) for year in years
        ]
        self.graduation_years_status = "known" if years else "unknown"

    __table_args__ = (
        CheckConstraint(
            "season IN ('autumn', 'spring', 'early', 'makeup', 'rolling', 'unknown')",
            name="chk_campaign_season",
        ),
        CheckConstraint(
            "recruitment_type IN ('campus_full_time', 'graduate_program', 'internship', 'unknown')",
            name="chk_campaign_recruitment_type",
        ),
        CheckConstraint(
            "internship_type IN ('not_applicable', 'summer', 'daily', 'winter', 'unknown')",
            name="chk_campaign_internship_type",
        ),
        CheckConstraint(
            "status IN ('upcoming', 'active', 'closed', 'unknown')",
            name="chk_campaign_status",
        ),
        CheckConstraint(
            "graduation_years_status IN ('known', 'unknown')",
            name="chk_campaign_graduation_years_status",
        ),
        CheckConstraint(
            "campaign_year IS NULL OR (campaign_year >= 2000 AND campaign_year <= 2200)",
            name="chk_campaign_year",
        ),
        CheckConstraint(
            "classification_confidence IS NULL OR "
            "(classification_confidence >= 0 AND classification_confidence <= 1)",
            name="chk_campaign_confidence",
        ),
        CheckConstraint(
            "last_seen_at >= first_seen_at",
            name="chk_campaign_seen_order",
        ),
        CheckConstraint(
            "start_at IS NULL OR deadline IS NULL OR deadline >= start_at",
            name="chk_campaign_date_order",
        ),
        UniqueConstraint(
            "id",
            "company_id",
            name="uq_campaign_identity_scope",
        ),
        Index(
            "idx_campaign_source_key",
            "company_id",
            "campaign_key",
            unique=True,
        ),
        Index("idx_campaign_company_status", "company_id", "status"),
        Index(
            "idx_campaign_deadline",
            "deadline",
            sqlite_where=_where_not_null("deadline"),
            postgresql_where=_where_not_null("deadline"),
        ),
    )


class CampaignGraduationYear(Base):
    """Cross-database, indexable graduation cohort for a campaign."""

    __tablename__ = "campaign_graduation_year"

    campaign_id = Column(
        Integer,
        ForeignKey("recruitment_campaign.id", ondelete="CASCADE"),
        primary_key=True,
    )
    graduation_year = Column(Integer, primary_key=True)

    campaign = relationship(
        "RecruitmentCampaign", back_populates="graduation_cohorts"
    )

    __table_args__ = (
        CheckConstraint(
            "graduation_year >= 2000 AND graduation_year <= 2200",
            name="chk_campaign_graduation_year",
        ),
        Index(
            "idx_campaign_graduation_year_lookup",
            "graduation_year",
            "campaign_id",
        ),
    )


class ObservedPositionRef(Base):
    """A public, lightweight position reference; never stores the full JD."""

    __tablename__ = "observed_position_ref"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    campaign_id = Column(Integer)
    source_id = Column(Text, nullable=False)
    dedupe_key = Column(Text, nullable=False)
    identity_kind = Column(Text, nullable=False)
    external_job_id = Column(Text)
    canonical_url = Column(Text)
    title = Column(Text, nullable=False)
    locations = Column(
        JSON,
        nullable=False,
        default=list,
        server_default=_sa_text("'[]'"),
    )
    category = Column(Text, nullable=False, default="unknown")
    recruitment_type = Column(Text, nullable=False, default="unknown")
    internship_type = Column(Text, nullable=False, default="not_applicable")
    graduation_years = Column(
        JSON,
        nullable=False,
        default=list,
        server_default=_sa_text("'[]'"),
    )
    first_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime)
    status = Column(Text, nullable=False, default="open")
    content_fingerprint = Column(Text, nullable=False)
    missing_count = Column(Integer, nullable=False, default=0)
    classification_confidence = Column(Float)
    classification_evidence = Column(
        JSON,
        nullable=False,
        default=dict,
        server_default=_sa_text("'{}'"),
    )

    company = relationship("Company", back_populates="observed_positions")
    campaign = relationship(
        "RecruitmentCampaign",
        back_populates="observed_positions",
        viewonly=True,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["campaign_id", "company_id"],
            [
                "recruitment_campaign.id",
                "recruitment_campaign.company_id",
            ],
            name="fk_position_ref_campaign_scope",
        ),
        CheckConstraint(
            "status IN ('open', 'closed', 'unknown')",
            name="chk_position_ref_status",
        ),
        CheckConstraint(
            "identity_kind IN ('external_id', 'canonical_url', 'fingerprint')",
            name="chk_position_ref_identity_kind",
        ),
        CheckConstraint(
            "(identity_kind <> 'external_id' OR external_job_id IS NOT NULL) AND "
            "(identity_kind <> 'canonical_url' OR canonical_url IS NOT NULL)",
            name="chk_position_ref_identity_evidence",
        ),
        CheckConstraint(
            "recruitment_type IN ('campus_full_time', 'graduate_program', 'internship', 'unknown')",
            name="chk_position_ref_recruitment_type",
        ),
        CheckConstraint(
            "internship_type IN ('not_applicable', 'summer', 'daily', 'winter', 'unknown')",
            name="chk_position_ref_internship_type",
        ),
        CheckConstraint("missing_count >= 0", name="chk_position_ref_missing_count"),
        CheckConstraint(
            "classification_confidence IS NULL OR "
            "(classification_confidence >= 0 AND classification_confidence <= 1)",
            name="chk_position_ref_confidence",
        ),
        CheckConstraint(
            "last_seen_at >= first_seen_at",
            name="chk_position_ref_seen_order",
        ),
        CheckConstraint(
            "(status = 'closed' AND closed_at IS NOT NULL) OR "
            "(status <> 'closed' AND closed_at IS NULL)",
            name="chk_position_ref_closed_time",
        ),
        Index(
            "idx_position_ref_source_dedupe",
            "source_id",
            "dedupe_key",
            unique=True,
        ),
        Index("idx_position_ref_company_status", "company_id", "status"),
        Index("idx_position_ref_campaign", "campaign_id"),
        Index("idx_position_ref_last_seen", "source_id", "last_seen_at"),
    )


class SourceSnapshot(Base):
    """One reconciled or failed observation of an official position source."""

    __tablename__ = "source_snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    source_id = Column(Text, nullable=False)
    run_key = Column(Text, nullable=False)
    crawl_log_id = Column(Integer, ForeignKey("crawl_log.id"))
    previous_valid_snapshot_id = Column(Integer)
    status = Column(Text, nullable=False)
    is_baseline = Column(Boolean, nullable=False, default=False)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)
    source_total = Column(Integer)
    fetched_total = Column(Integer, nullable=False, default=0)
    indexed_total = Column(Integer, nullable=False, default=0)
    excluded_total = Column(Integer, nullable=False, default=0)
    failed_total = Column(Integer, nullable=False, default=0)
    position_keys = Column(
        JSON,
        nullable=False,
        default=list,
        server_default=_sa_text("'[]'"),
    )
    position_set_hash = Column(Text)
    response_hash = Column(Text)
    parser_version = Column(Text, nullable=False)
    completeness_status = Column(Text, nullable=False)
    comparison_status = Column(Text, nullable=False, default="pending")
    error = Column(Text)

    company = relationship("Company", back_populates="source_snapshots")
    previous_valid_snapshot = relationship(
        "SourceSnapshot",
        remote_side=[id, company_id, source_id],
        foreign_keys=[previous_valid_snapshot_id, company_id, source_id],
        viewonly=True,
    )
    change_events = relationship(
        "CompanyChangeEvent", back_populates="snapshot", viewonly=True
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed')", name="chk_snapshot_status"
        ),
        CheckConstraint(
            "completeness_status IN "
            "('count_matched', 'pagination_verified', 'incomplete', 'failed')",
            name="chk_snapshot_completeness_status",
        ),
        CheckConstraint(
            "comparison_status IN "
            "('pending', 'baseline', 'compared', 'suppressed', 'failed')",
            name="chk_snapshot_comparison_status",
        ),
        CheckConstraint(
            "(comparison_status = 'baseline' AND is_baseline = TRUE) OR "
            "(comparison_status <> 'baseline' AND is_baseline = FALSE)",
            name="chk_snapshot_baseline_identity",
        ),
        CheckConstraint(
            "comparison_status <> 'baseline' OR "
            "(status = 'success' AND "
            "completeness_status IN ('count_matched', 'pagination_verified') AND "
            "previous_valid_snapshot_id IS NULL)",
            name="chk_snapshot_baseline_valid",
        ),
        CheckConstraint(
            "comparison_status <> 'compared' OR "
            "(status = 'success' AND "
            "completeness_status IN ('count_matched', 'pagination_verified') AND "
            "previous_valid_snapshot_id IS NOT NULL AND is_baseline = FALSE)",
            name="chk_snapshot_compared_valid",
        ),
        CheckConstraint(
            "status <> 'failed' OR comparison_status = 'failed'",
            name="chk_snapshot_failed_comparison",
        ),
        CheckConstraint(
            "(source_total IS NULL OR source_total >= 0) AND "
            "fetched_total >= 0 AND indexed_total >= 0 AND "
            "excluded_total >= 0 AND failed_total >= 0",
            name="chk_snapshot_counts",
        ),
        CheckConstraint(
            "fetched_total = indexed_total + excluded_total + failed_total",
            name="chk_snapshot_accounted_counts",
        ),
        CheckConstraint(
            "completeness_status <> 'count_matched' OR "
            "(source_total IS NOT NULL AND source_total = fetched_total)",
            name="chk_snapshot_source_total_matched",
        ),
        CheckConstraint(
            "comparison_status NOT IN ('baseline', 'compared') OR "
            "(completed_at IS NOT NULL AND position_set_hash IS NOT NULL)",
            name="chk_snapshot_comparison_evidence",
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= fetched_at",
            name="chk_snapshot_time_order",
        ),
        UniqueConstraint(
            "id",
            "company_id",
            "source_id",
            name="uq_snapshot_identity_scope",
        ),
        ForeignKeyConstraint(
            ["previous_valid_snapshot_id", "company_id", "source_id"],
            [
                "source_snapshot.id",
                "source_snapshot.company_id",
                "source_snapshot.source_id",
            ],
            name="fk_snapshot_previous_scope",
        ),
        Index("idx_snapshot_source_fetched", "source_id", "fetched_at"),
        Index(
            "idx_snapshot_source_run_key",
            "source_id",
            "run_key",
            unique=True,
        ),
        Index(
            "idx_snapshot_one_baseline_per_source",
            "source_id",
            unique=True,
            sqlite_where=_sa_text("comparison_status = 'baseline'"),
            postgresql_where=_sa_text("comparison_status = 'baseline'"),
        ),
        Index(
            "idx_snapshot_one_comparison_per_previous",
            "previous_valid_snapshot_id",
            unique=True,
            sqlite_where=_sa_text("comparison_status = 'compared'"),
            postgresql_where=_sa_text("comparison_status = 'compared'"),
        ),
        Index("idx_snapshot_company_fetched", "company_id", "fetched_at"),
        Index("idx_snapshot_previous_valid", "previous_valid_snapshot_id"),
        Index("idx_snapshot_status", "status", "completeness_status"),
    )


class CompanyChangeEvent(Base):
    """Auditable company-level change used by the global M1 dashboard."""

    __tablename__ = "company_change_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    campaign_id = Column(Integer)
    snapshot_id = Column(Integer, nullable=False)
    source_id = Column(Text, nullable=False)
    dedup_key = Column(Text, nullable=False, unique=True)
    event_type = Column(Text, nullable=False)
    added_count = Column(Integer, nullable=False, default=0)
    reopened_count = Column(Integer, nullable=False, default=0)
    closed_count = Column(Integer, nullable=False, default=0)
    changed_count = Column(Integer, nullable=False, default=0)
    reporting_date_cn = Column(Date, nullable=False)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    computation_status = Column(Text, nullable=False, default="computed")
    evidence = Column(
        JSON,
        nullable=False,
        default=dict,
        server_default=_sa_text("'{}'"),
    )

    company = relationship("Company", back_populates="change_events")
    campaign = relationship(
        "RecruitmentCampaign", back_populates="change_events", viewonly=True
    )
    snapshot = relationship(
        "SourceSnapshot", back_populates="change_events", viewonly=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["campaign_id", "company_id"],
            [
                "recruitment_campaign.id",
                "recruitment_campaign.company_id",
            ],
            name="fk_company_change_campaign_scope",
        ),
        ForeignKeyConstraint(
            ["snapshot_id", "company_id", "source_id"],
            [
                "source_snapshot.id",
                "source_snapshot.company_id",
                "source_snapshot.source_id",
            ],
            name="fk_company_change_snapshot_scope",
        ),
        CheckConstraint(
            "event_type IN ('campaign_started', 'campaign_updated', "
            "'campaign_closed', 'positions_changed', 'position_reopened', "
            "'page_updated', 'source_degraded', 'source_recovered')",
            name="chk_company_change_event_type",
        ),
        CheckConstraint(
            "computation_status IN ('computed', 'suppressed', 'review_required')",
            name="chk_company_change_computation_status",
        ),
        CheckConstraint(
            "added_count >= 0 AND reopened_count >= 0 AND "
            "closed_count >= 0 AND changed_count >= 0",
            name="chk_company_change_counts",
        ),
        CheckConstraint(
            "event_type <> 'positions_changed' OR "
            "(added_count + closed_count + changed_count > 0 AND "
            "reopened_count = 0)",
            name="chk_company_change_positions_counts",
        ),
        CheckConstraint(
            "event_type <> 'position_reopened' OR "
            "(reopened_count > 0 AND added_count = 0 AND "
            "closed_count = 0 AND changed_count = 0)",
            name="chk_company_change_reopened_counts",
        ),
        CheckConstraint(
            "event_type IN ('positions_changed', 'position_reopened') OR "
            "(added_count = 0 AND reopened_count = 0 AND "
            "closed_count = 0 AND changed_count = 0)",
            name="chk_company_change_non_position_counts",
        ),
        CheckConstraint(
            "event_type NOT IN "
            "('campaign_started', 'campaign_updated', 'campaign_closed') OR "
            "campaign_id IS NOT NULL",
            name="chk_company_change_campaign_required",
        ),
        Index("idx_company_change_date", "reporting_date_cn", "event_type"),
        Index("idx_company_change_company", "company_id", "occurred_at"),
        Index("idx_company_change_snapshot", "snapshot_id"),
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


@sa_event.listens_for(Company, "before_update")
def _company_before_update(mapper, connection, target):
    target.updated_at = datetime.utcnow()
