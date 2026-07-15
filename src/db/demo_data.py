"""可重复的 JobPulse 产品演示数据。"""

from datetime import datetime, timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from src.db.models import (
    ACTION_FAVORITED,
    ACTION_TO_APPLY,
    APP_APPLIED,
    APP_INTERVIEWING,
    APP_OFFER_PENDING,
    APP_REJECTED,
    APP_TEST,
    Application,
    ApplicationEvent,
    Company,
    CrawlLog,
    EVT_INTERVIEW,
    EVT_STATUS_CHANGE,
    EVT_TEST,
    Job,
    Subscription,
    UserJobAction,
)


def _clear_demo_tables(db: Session) -> None:
    """按外键依赖顺序清空产品数据，保留数据库结构。"""
    for model in (
        ApplicationEvent,
        Application,
        UserJobAction,
        Subscription,
        CrawlLog,
        Company,
        Job,
    ):
        db.execute(delete(model))


def _add_application(
    db: Session,
    job: Job,
    statuses: list[str],
    *,
    now: datetime,
    age_days: int,
    notes: str,
) -> Application:
    applied_at = now - timedelta(days=age_days)
    latest_at = applied_at + timedelta(days=max(0, len(statuses) - 1) * 2)
    application = Application(
        job_id=job.id,
        status=statuses[-1],
        applied_at=applied_at,
        updated_at=latest_at,
        notes=notes,
    )
    db.add(application)
    db.flush()

    previous = None
    for index, status in enumerate(statuses):
        db.add(
            ApplicationEvent(
                application_id=application.id,
                event_type=EVT_STATUS_CHANGE,
                from_status=previous,
                to_status=status,
                occurred_at=applied_at + timedelta(days=index * 2),
                is_correction=False,
            )
        )
        previous = status
    return application


def seed_demo_data(db: Session, *, replace: bool = False) -> dict[str, int]:
    """写入完整演示场景，返回可展示的实体计数。"""
    if replace:
        _clear_demo_tables(db)
        db.flush()
    elif db.query(Job).count() > 0:
        return {
            "jobs": db.query(Job).count(),
            "applications": db.query(Application).count(),
            "saved_jobs": db.query(UserJobAction).filter(UserJobAction.ended_at.is_(None)).count(),
            "subscriptions": db.query(Subscription).count(),
        }

    now = datetime.utcnow()
    companies = [
        Company(name="字节跳动", industry="互联网", category="互联网大厂"),
        Company(name="美团", industry="本地生活", category="互联网大厂"),
        Company(name="腾讯", industry="互联网", category="互联网大厂"),
        Company(name="小米", industry="智能硬件", category="科技公司"),
        Company(name="阿里巴巴", industry="电子商务", category="互联网大厂"),
        Company(name="哔哩哔哩", industry="内容社区", category="成长公司"),
        Company(name="大疆", industry="智能硬件", category="科技公司"),
        Company(name="MiniMax", industry="人工智能", category="AI 公司"),
    ]
    db.add_all(companies)

    job_specs = [
        ("字节跳动", "产品经理", "北京", "25-45K", "boss", "负责内容产品策略、需求分析与跨团队推进。", False, True),
        ("美团", "增长产品经理", "上海", "25-40K", "lagou", "围绕用户增长设计实验，并持续复盘关键转化。", False, False),
        ("腾讯", "产品策划", "深圳", "20-35K", "nowcoder", "参与社交产品规划，完成从洞察到上线的完整闭环。", False, True),
        ("小米", "产品实习生", "北京", "250-350/天", "company", "协助智能硬件产品调研、体验分析与版本跟进。", True, True),
        ("阿里巴巴", "电商产品经理", "杭州", "25-45K", "company", "设计商家经营工具，提升供给效率与交易体验。", False, False),
        ("哔哩哔哩", "社区产品经理", "上海", "20-35K", "boss", "理解社区生态，推动创作者与用户体验优化。", False, True),
        ("大疆", "硬件产品经理", "深圳", "25-40K", "company", "定义软硬件一体化体验并协调研发交付。", False, False),
        ("MiniMax", "AI 产品经理", "北京", "30-50K", "lagou", "探索大模型产品场景，快速验证并推动能力落地。", False, True),
    ]
    jobs = [
        Job(
            company=company,
            title=title,
            location=location,
            salary=salary,
            source=source,
            jd=jd,
            job_category="product",
            is_intern=is_intern,
            is_fresh=is_fresh,
            collected_at=now - timedelta(hours=index * 7),
            published_at=now - timedelta(days=index + 1),
            deadline=now + timedelta(days=12 + index * 3),
        )
        for index, (company, title, location, salary, source, jd, is_intern, is_fresh) in enumerate(job_specs)
    ]
    db.add_all(jobs)
    db.flush()

    applications = [
        _add_application(db, jobs[0], [APP_APPLIED, APP_TEST], now=now, age_days=8, notes="已完成网申，等待笔试"),
        _add_application(db, jobs[1], [APP_APPLIED, APP_INTERVIEWING], now=now, age_days=7, notes="一面重点准备增长案例"),
        _add_application(db, jobs[2], [APP_APPLIED], now=now, age_days=4, notes="通过官网投递"),
        _add_application(db, jobs[3], [APP_APPLIED, APP_INTERVIEWING, APP_OFFER_PENDING], now=now, age_days=12, notes="等待 Offer 审批"),
        _add_application(db, jobs[4], [APP_APPLIED, APP_REJECTED], now=now, age_days=15, notes="流程已结束，保留复盘"),
    ]

    db.add_all(
        [
            ApplicationEvent(
                application_id=applications[0].id,
                event_type=EVT_TEST,
                scheduled_at=now + timedelta(days=2, hours=2),
                note="在线产品分析测评",
            ),
            ApplicationEvent(
                application_id=applications[1].id,
                event_type=EVT_INTERVIEW,
                round=2,
                scheduled_at=now + timedelta(days=3, hours=5),
                note="业务负责人面试",
            ),
        ]
    )

    db.add_all(
        [
            UserJobAction(job_id=jobs[5].id, action_type=ACTION_FAVORITED),
            UserJobAction(job_id=jobs[6].id, action_type=ACTION_FAVORITED),
            UserJobAction(job_id=jobs[6].id, action_type=ACTION_TO_APPLY),
            UserJobAction(job_id=jobs[7].id, action_type=ACTION_TO_APPLY),
        ]
    )
    db.add_all(
        [
            Subscription(keyword="产品经理", location="北京"),
            Subscription(keyword="AI 产品", company="MiniMax"),
            Subscription(company="大疆", location="深圳"),
        ]
    )
    db.add_all(
        [
            CrawlLog(source="boss", status="success", count=12, started_at=now - timedelta(hours=2), finished_at=now - timedelta(hours=2, minutes=-3)),
            CrawlLog(source="lagou", status="success", count=8, started_at=now - timedelta(hours=1), finished_at=now - timedelta(minutes=56)),
        ]
    )
    db.commit()

    return {
        "jobs": len(jobs),
        "applications": len(applications),
        "saved_jobs": 4,
        "subscriptions": 3,
    }
