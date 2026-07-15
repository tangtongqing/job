"""数据库初始化脚本：建表 + 填演示种子数据。

用法：
    python -m src.db.init_db

验证用，非生产数据。种子数据对应 web/dashboard-data.ts 的演示数据，
确保前后端演示数据一致。
"""

from datetime import datetime, timedelta

from src.db.session import engine, SessionLocal, Base
from src.db.models import (
    Job,
    Application,
    ApplicationEvent,
    Company,
    Subscription,
    CrawlLog,
    APP_APPLIED,
    APP_TEST,
    APP_INTERVIEWING,
    APP_OFFER_ACCEPTED,
    EVT_STATUS_CHANGE,
)
from src.core.statemachine import transition


def init_db():
    """建表 + 种子数据。"""
    # 建表
    Base.metadata.create_all(engine)
    print("[init_db] 表已创建")

    db = SessionLocal()
    try:
        # 检查是否已有数据
        if db.query(Job).count() > 0:
            print("[init_db] 已有数据，跳过种子")
            return

        # 4 家公司（对应 dashboard-data.ts 的字节/美团/腾讯/小米）
        companies = [
            Company(name="字节跳动", industry="互联网", category="互联网大厂"),
            Company(name="美团", industry="互联网", category="互联网大厂"),
            Company(name="腾讯", industry="互联网", category="互联网大厂"),
            Company(name="小米", industry="智能硬件", category="互联网大厂"),
        ]
        db.add_all(companies)
        db.flush()  # 拿 id

        # 4 个岗位
        jobs = [
            Job(
                company="字节跳动",
                title="产品经理",
                location="北京",
                source="boss",
                job_category="product",
                is_fresh=True,
            ),
            Job(
                company="美团",
                title="高级产品经理",
                location="上海",
                source="lagou",
                job_category="product",
            ),
            Job(
                company="腾讯",
                title="产品策划",
                location="深圳",
                source="nowcoder",
                job_category="product",
                is_fresh=True,
            ),
            Job(
                company="小米",
                title="产品实习",
                location="北京",
                source="company",
                job_category="product",
                is_intern=True,
            ),
        ]
        db.add_all(jobs)
        db.flush()

        # 4 个投递，用状态机流转（验证状态机 + 事件表）
        # 1. 字节 → applied → test
        app1 = Application(job_id=jobs[0].id, status=APP_APPLIED)
        db.add(app1)
        db.flush()
        transition(db, app1.id, APP_TEST)

        # 2. 美团 → applied → interviewing
        app2 = Application(job_id=jobs[1].id, status=APP_APPLIED)
        db.add(app2)
        db.flush()
        transition(db, app2.id, APP_INTERVIEWING)

        # 3. 腾讯 → applied（只投递）
        app3 = Application(job_id=jobs[2].id, status=APP_APPLIED)
        db.add(app3)

        # 4. 小米 → applied → ... → offer_accepted
        app4 = Application(job_id=jobs[3].id, status=APP_APPLIED)
        db.add(app4)
        db.flush()
        transition(db, app4.id, APP_TEST)
        transition(db, app4.id, APP_INTERVIEWING)
        from src.db.models import APP_OFFER_PENDING
        transition(db, app4.id, APP_OFFER_PENDING)
        transition(db, app4.id, APP_OFFER_ACCEPTED)

        db.commit()
        print(f"[init_db] 种子数据已插入：{len(companies)} 公司 / {len(jobs)} 岗位 / 4 投递")

        # 验证事件表
        evt_count = db.query(ApplicationEvent).count()
        print(f"[init_db] ApplicationEvent 记录：{evt_count} 条")

    finally:
        db.close()


if __name__ == "__main__":
    init_db()
