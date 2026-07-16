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


def _demo_jd(spec: dict) -> str:
    """Build a substantial, deterministic JD for an explicitly demo job."""
    return "\n".join(
        [
            "岗位职责",
            f"1. 负责{spec['focus']}的产品规划，围绕{spec['area']}识别真实用户问题并定义阶段性路线图。",
            "2. 通过用户访谈、数据分析和竞品研究拆解需求，输出可执行的 PRD、原型与验收标准。",
            f"3. 协同{spec['partners']}推进方案设计、研发、测试和上线，主动管理风险与依赖。",
            f"4. 建立{spec['metric']}指标体系，持续复盘产品表现并推动迭代。",
            "5. 沉淀关键决策、实验结果和上线复盘，使跨团队协作过程可追溯。",
        ]
    )


def _demo_requirement(spec: dict) -> str:
    return "\n".join(
        [
            "任职要求",
            f"1. {spec['education']}及以上学历，{spec['experience']}相关产品、设计或数据分析经历。",
            f"2. 能够清晰拆解{spec['skill']}，用结构化文档和数据说明判断。",
            "3. 具备良好的沟通、项目推进与优先级管理能力，能在不确定环境中交付结果。",
            f"4. 加分项：{spec['bonus']}。",
        ]
    )


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
    company_specs = [
        ("字节跳动", "互联网", "互联网大厂", "https://jobs.bytedance.com/"),
        ("美团", "本地生活", "互联网大厂", "https://zhaopin.meituan.com/"),
        ("腾讯", "互联网", "互联网大厂", "https://careers.tencent.com/zh-cn/"),
        ("小米", "智能硬件", "科技公司", "https://hr.xiaomi.com/website"),
        ("阿里巴巴", "电子商务", "互联网大厂", "https://talent.alibaba.com/"),
        ("哔哩哔哩", "内容社区", "成长公司", "https://jobs.bilibili.com/"),
        ("大疆", "智能硬件", "科技公司", "https://we.dji.com/"),
        ("MiniMax", "人工智能", "AI 公司", "https://www.minimaxi.com/"),
        ("Figma", "设计协作", "SaaS", "https://www.figma.com/careers/"),
        ("Webflow", "网站建设", "SaaS", "https://webflow.com/careers"),
        ("Intercom", "客户服务", "SaaS", "https://www.intercom.com/careers"),
        ("Stripe", "支付基础设施", "SaaS", "https://stripe.com/jobs"),
    ]
    companies = [
        Company(name=name, industry=industry, category=category, website=website)
        for name, industry, category, website in company_specs
    ]
    db.add_all(companies)

    job_specs = [
        {"company": "字节跳动", "title": "内容产品经理", "location": "北京", "salary": "25-45K", "focus": "内容消费与推荐体验", "area": "浏览、互动和留存", "partners": "算法、设计和运营团队", "metric": "内容质量与用户活跃", "education": "本科", "experience": "3年以上", "skill": "内容供给与用户需求", "bonus": "有推荐或内容社区经验", "category": "product"},
        {"company": "美团", "title": "增长产品经理", "location": "上海", "salary": "25-40K", "focus": "用户增长与营销工具", "area": "拉新、转化和复购", "partners": "数据、研发和业务团队", "metric": "转化率与增量贡献", "education": "本科", "experience": "3-5年", "skill": "增长漏斗与实验设计", "bonus": "熟悉本地生活场景", "category": "product"},
        {"company": "腾讯", "title": "社交产品策划", "location": "深圳", "salary": "20-35K", "focus": "社交关系链与互动体验", "area": "沟通、关系和内容流通", "partners": "设计、研发和安全团队", "metric": "互动深度与用户留存", "education": "本科", "experience": "2年以上", "skill": "复杂社交场景与用户行为", "bonus": "对社区治理有实践", "category": "product"},
        {"company": "小米", "title": "智能硬件产品实习生", "location": "北京", "salary": "250-350/天", "focus": "智能家居软硬件体验", "area": "设备配网、控制和场景联动", "partners": "工业设计、硬件和客户端团队", "metric": "激活成功率与使用频次", "education": "本科", "experience": "实习", "skill": "软硬件一体化用户旅程", "bonus": "有 IoT 项目或硬件原型经验", "category": "product", "is_intern": True},
        {"company": "阿里巴巴", "title": "商家产品经理", "location": "杭州", "salary": "25-45K", "focus": "商家经营与供给效率", "area": "商品、库存和营销经营", "partners": "行业运营、研发和数据团队", "metric": "商家活跃与交易效率", "education": "本科", "experience": "3年以上", "skill": "B 端复杂流程与商业目标", "bonus": "有电商平台经验", "category": "product"},
        {"company": "哔哩哔哩", "title": "创作者产品经理", "location": "上海", "salary": "20-35K", "focus": "创作者生产与经营工具", "area": "创作、发布和粉丝经营", "partners": "社区运营、设计和研发团队", "metric": "优质内容供给与创作留存", "education": "本科", "experience": "2-4年", "skill": "创作者动机与社区生态", "bonus": "是深度内容创作者", "category": "product"},
        {"company": "大疆", "title": "移动端产品经理", "location": "深圳", "salary": "25-40K", "focus": "航拍应用与设备连接体验", "area": "飞行前准备、拍摄和素材管理", "partners": "硬件、影像和客户端团队", "metric": "连接稳定性与核心任务成功率", "education": "本科", "experience": "3年以上", "skill": "硬件限制下的移动交互", "bonus": "熟悉摄影或无人机", "category": "product"},
        {"company": "MiniMax", "title": "AI 产品经理", "location": "北京", "salary": "30-50K", "focus": "大模型应用与对话体验", "area": "任务理解、生成质量和安全", "partners": "算法、评测和工程团队", "metric": "任务成功率与用户满意度", "education": "本科", "experience": "3年以上", "skill": "模型能力边界与产品场景", "bonus": "有 LLM 评测或 Prompt 工程经验", "category": "product"},
        {"company": "Figma", "title": "Product Manager, Code", "location": "San Francisco / New York", "salary": "$169K-$303K", "focus": "设计到代码的产品工作流", "area": "设计系统、代码交付和团队协作", "partners": "设计、工程和开发者关系团队", "metric": "交付效率与开发者活跃", "education": "本科", "experience": "5年以上", "skill": "设计工具与开发流程", "bonus": "有设计系统或前端开发经验", "category": "product"},
        {"company": "Webflow", "title": "Senior Product Manager, Growth", "location": "Remote", "salary": "$160K-$240K", "focus": "网站建设用户的激活与增长", "area": "注册、首次发布和升级", "partners": "增长工程、设计和数据团队", "metric": "激活率、发布率和付费转化", "education": "本科", "experience": "5年以上", "skill": "PLG 增长漏斗与实验", "bonus": "有 SaaS 自助购买产品经验", "category": "product"},
        {"company": "Intercom", "title": "Senior Product Manager, AI", "location": "Dublin", "salary": "薪资面议", "focus": "AI 客服智能体与人机协作", "area": "意图理解、自助解决和升级人工", "partners": "机器学习、设计和客户成功团队", "metric": "问题解决率与客户满意度", "education": "本科", "experience": "5年以上", "skill": "AI 产品质量与客服流程", "bonus": "有智能客服或 LLM 产品经验", "category": "product"},
        {"company": "Stripe", "title": "Product Manager, Cash Platform", "location": "New York", "salary": "$180K-$280K", "focus": "企业资金与现金管理平台", "area": "资金归集、对账和流动性", "partners": "工程、风险和财务产品团队", "metric": "资金处理成功率与对账效率", "education": "本科", "experience": "5年以上", "skill": "支付基础设施与财务流程", "bonus": "有金融科技或平台产品经验", "category": "product"},
    ]
    # Add a second realistic product track for each company.  These remain
    # explicit demo snapshots; live jobs enter through the Greenhouse sources.
    second_tracks = [
        ("字节跳动", "AI 策略产品经理", "北京", "30-50K", "智能创作工具", "生成效果、可控性和使用留存"),
        ("美团", "商户平台产品经理", "北京", "25-45K", "商户履约与经营平台", "履约效率、异常率和商户满意度"),
        ("腾讯", "云产品经理", "深圳", "25-45K", "云端开发者体验", "激活、调用成功率和留存"),
        ("小米", "IoT 平台产品经理", "武汉", "20-35K", "IoT 设备接入平台", "接入周期、稳定性和开发者满意度"),
        ("阿里巴巴", "数据产品经理", "杭州", "25-45K", "商业数据分析平台", "数据准确性、查询效率和使用覆盖"),
        ("哔哩哔哩", "社区增长产品经理", "上海", "25-40K", "新用户社区融入", "关注转化、互动率和次日留存"),
        ("大疆", "影像产品经理", "深圳", "25-45K", "智能影像处理", "成片效率、功能渗透和导出成功率"),
        ("MiniMax", "AI 评测产品经理", "上海", "30-50K", "模型评测与质量平台", "评测覆盖、问题发现率和回归效率"),
        ("Figma", "Product Manager, Collaboration", "Remote", "$170K-$250K", "多人设计协作", "协作深度、共享转化和团队留存"),
        ("Webflow", "Product Manager, AI", "Remote", "$160K-$240K", "AI 网站搭建体验", "生成成功率、编辑深度和发布转化"),
        ("Intercom", "Product Manager, Fin", "Dublin", "薪资面议", "AI 客服解决率", "自助解决率、准确性和转人工比例"),
        ("Stripe", "Product Manager, Payments", "New York", "$180K-$280K", "支付平台与开发者体验", "支付成功率、接入周期和故障率"),
    ]
    website_map = {name: website for name, _, _, website in company_specs}
    base_by_company = {spec["company"]: spec for spec in job_specs}
    for company, title, location, salary, focus, metric in second_tracks:
        base = dict(base_by_company.get(company, job_specs[0]))
        base.update({"company": company, "title": title, "location": location, "salary": salary, "focus": focus, "metric": metric})
        job_specs.append(base)

    jobs = []
    for index, spec in enumerate(job_specs):
        official_url = website_map[spec["company"]]
        jobs.append(
            Job(
                company=spec["company"],
                title=spec["title"],
                location=spec["location"],
                salary=spec["salary"],
                source="demo_snapshot",
                source_url=official_url,
                apply_url=official_url,
                jd=_demo_jd(spec),
                requirement=_demo_requirement(spec),
                job_category=spec.get("category", "product"),
                graduation_year="2026-2027" if spec.get("is_intern") else "不限",
                education=spec["education"],
                experience=spec["experience"],
                is_intern=bool(spec.get("is_intern", False)),
                is_fresh=index < 7,
                collected_at=now - timedelta(hours=index * 4),
                published_at=now - timedelta(days=index % 10 + 1),
                deadline=now + timedelta(days=12 + index * 2),
                last_verified_at=now - timedelta(hours=index + 1),
            )
        )
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
            CrawlLog(
                source="demo_snapshot",
                status="skipped",
                count=0,
                error="演示数据已初始化；该记录不代表真实网络采集。",
                started_at=now,
                finished_at=now,
            ),
        ]
    )
    db.commit()

    return {
        "jobs": len(jobs),
        "applications": len(applications),
        "saved_jobs": 4,
        "subscriptions": 3,
    }
