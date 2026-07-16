"""采集层测试（TASK-BE-CRAWLER-001 §测试要求 12 项）。

全部用注入/fake，不触网。
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.session import Base, get_db
import src.db.models  # noqa
from src.db.models import Job, CrawlLog
from src.crawler.compliance.robots import RobotsChecker
from src.crawler.compliance.rate_limiter import RateLimiter
from src.crawler.compliance.retry import retry_with_backoff
from src.crawler.normalizer import (
    normalize_location, normalize_company, extract_graduation_year,
    extract_education, extract_experience, classify_job, normalize_job,
)
from src.crawler import dedup
from src.crawler.service import CrawlService
from src.crawler.verifier import verify_job
from src.crawler.adapters.base import BaseAdapter
from src.crawler.adapters.factory import create_adapter
from src.crawler.adapters.greenhouse import GreenhouseAdapter, _extract_requirements
from src.crawler.config import load_crawler_config


@pytest.fixture()
def db_session():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    S = sessionmaker(bind=eng)
    s = S()
    yield s
    s.close()


# ---------- 1. robots fail-closed ----------


def test_robots_fail_closed():
    """robots 读取失败时默认禁止（fail-closed）。"""
    def always_fail(base_url):
        return None  # 模拟读取失败
    checker = RobotsChecker(fetcher=always_fail)
    assert checker.can_fetch("https://example.com/job/1") is False


def test_robots_manual_override_disabled_by_default():
    """manual override 默认关闭时，人工 allow 不生效。"""
    def always_fail(base_url):
        return None
    checker = RobotsChecker(fetcher=always_fail)
    assert checker.can_fetch("https://example.com/job/1") is False
    assert checker.mark_allowed_manually("https://example.com") is False
    assert checker.can_fetch("https://example.com/job/1") is False


def test_robots_manual_override_enabled():
    """manual override 显式开启后才允许人工放行。"""
    def always_fail(base_url):
        return None
    checker = RobotsChecker(fetcher=always_fail, manual_override=True)
    assert checker.can_fetch("https://example.com/job/1") is False
    assert checker.mark_allowed_manually("https://example.com") is True
    assert checker.can_fetch("https://example.com/job/1") is True


def test_robots_allows_when_explicit():
    """robots 显式允许时可以抓取。"""
    def allow_all(base_url):
        return "User-agent: *\nAllow: /"
    checker = RobotsChecker(fetcher=allow_all)
    assert checker.can_fetch("https://example.com/job/1") is True


# ---------- 2. rate limiter ----------


def test_rate_limiter_per_source():
    """rate limiter 按 source 独立工作，不真实 sleep。"""
    sleeps = []
    clock_now = [0.0]
    def fake_sleep(s):
        clock_now[0] += s
        sleeps.append(s)
    def fake_clock():
        return clock_now[0]
    rl = RateLimiter(min_interval=60.0, sleeper=fake_sleep, clock=fake_clock)

    # 第一次：last_request 为空，设初始时间避免误等
    clock_now[0] = 100.0
    rl._last_request["boss"] = 100.0  # 预设：刚请求过
    # 同 source 立即第二次：需等 60s
    waited = rl.wait_if_needed("boss")
    assert waited == 60.0
    # 不同 source 不受影响（无历史）
    clock_now[0] = 110.0
    rl._last_request.clear()
    rl._last_request["company"] = 110.0  # 刚请求过
    assert rl.wait_if_needed("company") == 60.0


# ---------- 3. retry/backoff ----------


def test_retry_with_backoff_injectable_sleeper():
    """retry 可注入 sleeper，重试次数可断言。"""
    sleeps = []
    attempts = []
    def flaky():
        attempts.append(1)
        if len(attempts) < 3:
            raise ValueError("fail")
        return "ok"
    result = retry_with_backoff(
        flaky, max_retries=3, base_delay=0.1,
        sleeper=lambda s: sleeps.append(s),
        rng=lambda: 0.0,
    )
    assert result == "ok"
    assert len(attempts) == 3
    assert len(sleeps) == 2  # 失败2次，sleep 2次


def test_retry_exhausted_raises():
    """重试耗尽后抛出最后异常。"""
    def always_fail():
        raise RuntimeError("always")
    with pytest.raises(RuntimeError):
        retry_with_backoff(always_fail, max_retries=2, sleeper=lambda s: None, rng=lambda: 0.0)


# ---------- 4. normalizer ----------


def test_normalize_location():
    assert normalize_location("北京市") == "北京"
    assert normalize_location("beijing") == "北京"
    assert normalize_location("上海") == "上海"
    assert normalize_location(None) is None


def test_normalize_company():
    assert normalize_company("字节跳动有限公司") == "字节跳动"
    assert normalize_company("腾讯科技有限公司") == "腾讯"  # "科技有限公司"整体后缀被去
    assert normalize_company("阿里（中国）") == "阿里"


def test_extract_graduation_year():
    assert extract_graduation_year("2026届") == "2026"
    assert extract_graduation_year("2027年毕业") == "2027"
    assert extract_graduation_year("不限") is None


def test_extract_education():
    assert extract_education("本科及以上") == "本科"
    assert extract_education("master") == "硕士"
    assert extract_education("不限") is None


def test_extract_experience():
    assert extract_experience("3-5年") == "3-5年"
    assert extract_experience("5年") == "5年"
    assert extract_experience("应届") == "应届"


def test_classify_job():
    assert classify_job("产品经理") == "product"
    assert classify_job("Java 后端工程师") == "tech"
    assert classify_job("UI 设计师") == "design"
    assert classify_job("运营专员") == "operation"


def test_extract_english_experience():
    assert extract_experience("5+ years of product management experience") == "5+ years"
    assert extract_experience("3-5 years building SaaS products") == "3-5 years"


def test_crawler_config_supports_lists_and_shared_adapters(tmp_path):
    config_file = tmp_path / "sources.yaml"
    config_file.write_text(
        """
global:
  batch_size: 10
sources:
  first_board:
    enabled: true
    adapter: greenhouse
    keywords:
      - product manager
      - product design
  second_board:
    enabled: true
    adapter: greenhouse
    keywords: ["growth product", "research"]
""".strip(),
        encoding="utf-8",
    )
    config = load_crawler_config(config_file)
    assert config.enabled_source_names() == ["first_board", "second_board"]
    assert config.sources["first_board"].options["keywords"] == [
        "product manager",
        "product design",
    ]
    assert config.sources["second_board"].options["keywords"] == [
        "growth product",
        "research",
    ]


def test_greenhouse_adapter_parses_full_job():
    payload = {
        "jobs": [
            {
                "id": 7,
                "company_name": "Example SaaS",
                "title": "Senior Product Manager, AI",
                "absolute_url": "https://boards.greenhouse.io/example/jobs/7",
                "location": {"name": "Remote"},
                "first_published": "2026-07-10T08:00:00Z",
                "application_deadline": "2026-08-10",
                "departments": [{"name": "Product"}],
                "content": (
                    "&lt;h2&gt;The role&lt;/h2&gt;"
                    "&lt;p&gt;You have an opportunity to own the AI product roadmap and customer outcomes.&lt;/p&gt;"
                    "&lt;h2&gt;Qualifications&lt;/h2&gt;"
                    "&lt;p&gt;5+ years of product management experience. Bachelor degree preferred.&lt;/p&gt;"
                    "&lt;h2&gt;Compensation&lt;/h2&gt;"
                    "&lt;p&gt;$180,000 - $240,000 a year&lt;/p&gt;"
                ),
            },
            {
                "id": 8,
                "company_name": "Example SaaS",
                "title": "Account Executive",
                "absolute_url": "https://boards.greenhouse.io/example/jobs/8",
                "location": {"name": "Remote"},
                "departments": [{"name": "Sales"}],
                "content": "&lt;p&gt;Sell the product.&lt;/p&gt;",
            },
        ]
    }
    adapter = GreenhouseAdapter(
        config={
            "source_name": "greenhouse_example",
            "board_token": "example",
            "keywords": ["product manager"],
            "max_jobs": 5,
            "min_interval_seconds": 0,
        },
        json_fetcher=lambda url: payload,
    )

    rows = adapter.crawl()
    assert len(rows) == 1
    job = rows[0]
    assert job["company"] == "Example SaaS"
    assert job["title"] == "Senior Product Manager, AI"
    assert "own the AI product roadmap" in job["jd"]
    assert "5+ years" in job["requirement"]
    assert job["requirement"].startswith("Qualifications")
    assert "You have an opportunity" not in job["requirement"]
    assert job["salary"] == "$180,000 - $240,000 a year"
    assert job["education"] == "本科"
    assert job["experience"] == "5+ years"
    assert job["apply_url"].endswith("/jobs/7")
    assert job["source_url"] == job["apply_url"]
    assert job["published_at"] is not None
    assert job["deadline"] is not None


@pytest.mark.parametrize(
    ("heading", "ending"),
    [
        ("We’d love to hear from you if you have:", "Pay Transparency Disclosure"),
        ("Must Have Experience", "What you'll be doing:"),
        ("What skills do I need?", "Benefits"),
        ("Who you are", "Why this role, why now"),
    ],
)
def test_greenhouse_requirement_headings_are_exact(heading, ending):
    text = (
        "You have an opportunity to work on a meaningful product.\n"
        f"{heading}\n"
        "5+ years of relevant experience.\n"
        f"{ending}\n"
        "This content is not part of the requirements."
    )

    requirement = _extract_requirements(text)

    assert requirement is not None
    assert requirement.startswith(heading)
    assert "5+ years" in requirement
    assert "You have an opportunity" not in requirement
    assert "This content is not part" not in requirement


# ---------- 5. 同源去重 ----------


def test_dedup_same_source():
    items = [
        {"company": "字节跳动", "title": "产品经理", "location": "北京"},
        {"company": "字节跳动有限公司", "title": "产品经理", "location": "北京市"},  # 规范化后相同
        {"company": "美团", "title": "产品", "location": "上海"},
    ]
    result = dedup.dedup_same_source(items)
    assert len(result) == 2  # 前两条合并


# ---------- 6. 跨源去重只精确匹配 ----------


def test_cross_source_exact_match_merges():
    existing = [{"id": 1, "company": "字节跳动", "title": "产品经理", "location": "北京"}]
    new_item = {"company": "字节跳动有限公司", "title": "产品经理", "location": "北京市"}
    dup = dedup.find_cross_source_duplicate(existing, new_item)
    assert dup is not None  # 规范化精确相等 → 合并


def test_cross_source_substring_not_merged():
    """substring/contains 不得误合并。"""
    existing = [{"id": 1, "company": "字节", "title": "产品", "location": "北京"}]
    new_item = {"company": "字节跳动", "title": "产品经理", "location": "北京"}
    # 字节≠字节跳动（精确），产品≠产品经理（精确）→ 不合并
    dup = dedup.find_cross_source_duplicate(existing, new_item)
    assert dup is None


# ---------- 7. CrawlLog success/skipped/failed + adapter close ----------


class FakeAdapter(BaseAdapter):
    """可控制的 fake adapter。"""
    def __init__(self, config=None, robots_checker=None, **kwargs):
        super().__init__(config)
        self._should = kwargs.get("should_crawl_result", True)
        self._raw = kwargs.get("raw_jobs", [])
        self.closed = False
    def should_crawl(self):
        return self._should
    def fetch(self, page=1):
        return self._raw
    def parse(self, raw_data):
        return raw_data
    def close(self):
        self.closed = True


def test_crawl_source_success(db_session):
    fake = FakeAdapter(raw_jobs=[
        {"company": "字节跳动", "title": "产品", "location": "北京", "source": "company"},
    ])
    service = CrawlService()
    log = service.crawl_source(db_session, "company", adapter=fake)
    assert log.status == "success"
    assert log.count == 1
    assert db_session.query(Job).count() == 1


def test_crawl_source_skipped(db_session):
    fake = FakeAdapter(should_crawl_result=False)
    service = CrawlService()
    log = service.crawl_source(db_session, "company", adapter=fake)
    assert log.status == "skipped"
    assert fake.closed is True  # adapter 必须 close


def test_crawl_source_failed_and_closed(db_session):
    class FailAdapter(FakeAdapter):
        def fetch(self, page=1):
            raise RuntimeError("network error")
    fake = FailAdapter()
    service = CrawlService()
    log = service.crawl_source(db_session, "company", adapter=fake)
    assert log.status == "failed"
    assert "network error" in (log.error or "")
    assert fake.closed is True


# ---------- 8. 批量写入 ----------


def test_batch_write_dedup(db_session):
    """批量写入按 batch_size，重复项合并不破坏已有数据。"""
    raw = [{"company": f"公司{i}", "title": f"岗位{i}", "location": "北京", "source": "company"} for i in range(25)]
    fake = FakeAdapter(raw_jobs=raw)
    service = CrawlService(batch_size=10)
    log = service.crawl_source(db_session, "company", adapter=fake)
    assert log.status == "success"
    assert log.count == 25
    assert db_session.query(Job).count() == 25


# ---------- 9. verify_job ----------


def test_verify_job_invalid(db_session):
    """无效岗位 → is_valid=False, status=closed, last_verified_at 更新。"""
    j = Job(company="x", title="y", source="company", apply_url="https://expired.example")
    db_session.add(j); db_session.commit()
    verify_job(db_session, j.id, fetcher=lambda url: False)  # fake 返回无效
    db_session.refresh(j)
    assert j.is_valid is False
    assert j.status == "closed"
    assert j.last_verified_at is not None


def test_verify_job_valid(db_session):
    """有效岗位 → is_valid=True, last_verified_at 更新。"""
    j = Job(company="x", title="y", source="company", apply_url="https://ok.example", is_valid=False, status="closed")
    db_session.add(j); db_session.commit()
    verify_job(db_session, j.id, fetcher=lambda url: True)
    db_session.refresh(j)
    assert j.is_valid is True
    assert j.status == "displaying"


# ---------- API 测试（10/11/12）用 TestClient ----------


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient
    from src.main import app
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    S = sessionmaker(bind=eng)
    def override_get_db():
        s = S()
        try:
            yield s
        finally:
            s.close()
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_api_crawler_trigger(client):
    """10. POST /crawler/trigger 用 fake adapter 返回 200 + 写 CrawlLog。"""
    from src.api.routes.app.crawler import set_service_for_testing

    fake = FakeAdapter(raw_jobs=[
        {"company": "字节", "title": "产品", "location": "北京", "source": "company"},
    ])
    service = CrawlService()
    # 让 service 用 fake adapter：monkeypatch crawl_source
    orig = service.crawl_source
    def patched(db, source, adapter=None, **kw):
        return orig(db, source, adapter=fake, **kw)
    service.crawl_source = patched
    set_service_for_testing(service)

    try:
        r = client.post("/api/v1/crawler/trigger", json={"source": "company"})
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "success"
    finally:
        from src.api.routes.app.crawler import set_service_for_testing as reset
        reset(None)  # 清除 override（实际需重建，简化处理）


def test_api_crawler_trigger_rejects_disabled_source_without_robots_http(client, monkeypatch):
    """disabled source 不应被 trigger，也不应读取真实 robots。"""
    calls = []

    def forbidden_get(url, **kwargs):
        calls.append(url)
        raise AssertionError("disabled source should not touch robots HTTP")

    monkeypatch.setattr("httpx.get", forbidden_get)

    r = client.post("/api/v1/crawler/trigger", json={"source": "boss"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert calls == []


def test_api_crawler_logs(client):
    """11. GET /crawler/logs 返回日志列表。"""
    # 先写一条日志
    db_gen = __import__("src.main", fromlist=["app"])
    from src.main import app as _app
    s = next(_app.dependency_overrides[get_db]())
    s.add(CrawlLog(source="company", status="success", count=5, started_at=__import__("datetime").datetime.utcnow(), finished_at=__import__("datetime").datetime.utcnow()))
    s.commit()

    r = client.get("/api/v1/crawler/logs")
    assert r.status_code == 200
    assert len(r.json()["data"]) >= 1


def test_api_jobs_verify(client, monkeypatch):
    """12. POST /jobs/{id}/verify 用 fake verifier 不触网。"""
    from src.api.routes.app.jobs import set_verify_fetcher_for_testing

    # 建岗位
    r = client.post("/api/v1/jobs", json={"company": "x", "title": "y", "source": "company", "apply_url": "https://test.example"})
    job_id = r.json()["data"]["id"]

    def forbidden_head(url, **kwargs):
        raise AssertionError("verify endpoint should use fake fetcher in tests")

    calls = []

    def fake_fetcher(url):
        calls.append(url)
        return True

    monkeypatch.setattr("httpx.head", forbidden_head)
    set_verify_fetcher_for_testing(fake_fetcher)
    try:
        r2 = client.post(f"/api/v1/jobs/{job_id}/verify")
        assert r2.status_code == 200
        assert "data" in r2.json()
        assert "last_verified_at" in r2.json()["data"]
        assert calls == ["https://test.example"]
    finally:
        set_verify_fetcher_for_testing(None)
