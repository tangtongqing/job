"""AI 解析层测试（TASK-BE-AI-001 §测试要求 14 项）。

全部用注入/fake，禁止调用真实 LLM 或网络。
"""

import asyncio
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.session import Base, get_db
import src.db.models  # noqa
from src.db.models import Application, Job, ApplicationEvent, APP_APPLIED, APP_TEST
from src.core.ai import (
    RegexParser, AIParser, ApplicationMatcher,
    TTLCache, text_hash, AIRateLimiter,
    ParsedEmailResult,
)


# ---------- 1-2. RegexParser ----------


def test_regex_parser_companies_and_statuses():
    """1. 正则识别公司 + 5 类状态。"""
    rp = RegexParser()

    # 字节 + 面试
    r = rp.parse("您好，恭喜通过字节跳动笔试，邀请您参加面试")
    assert r.parsed is True
    assert r.company == "字节跳动"
    assert r.suggested_status == "interviewing"
    assert r.degraded is True
    assert r.confidence == 0.5

    # 腾讯 + offer
    r = rp.parse("腾讯给您发放 offer，请确认薪资")
    assert r.company == "腾讯"
    assert r.suggested_status == "offer_pending"

    # 阿里 + rejected
    r = rp.parse("很遗憾，您未能通过阿里巴巴的面试")
    assert r.company == "阿里巴巴"
    assert r.suggested_status == "rejected"  # 优先级最高

    # 美团 + 笔试
    r = rp.parse("美团笔试测评通知")
    assert r.company == "美团"
    assert r.suggested_status == "test"

    # 百度 + applied
    r = rp.parse("百度：您的简历已收到")
    assert r.company == "百度"
    assert r.suggested_status == "applied"


def test_regex_parser_fail_returns_parsed_false():
    """2. 正则失败返回 parsed=false。"""
    rp = RegexParser()
    r = rp.parse("今天天气不错，适合散步")
    assert r.parsed is False
    assert r.degraded is True


def test_regex_parser_extracts_demo_company_and_job_title():
    """降级模式也应能识别演示岗位中的公司和岗位，便于准确匹配投递记录。"""
    result = RegexParser().parse(
        "MiniMax AI 产品经理面试通知：恭喜您进入面试环节，请于明天下午参加业务面试。"
    )

    assert result.parsed is True
    assert result.company == "MiniMax"
    assert result.title == "AI 产品经理"
    assert result.suggested_status == "interviewing"


# ---------- 3. AIParser 无 Key 降级 ----------


def test_ai_parser_no_key_degrades_to_regex():
    """3. 无 API Key 时不调 LLM，直接正则降级。"""
    call_count = 0

    class FakeClient:
        async def call(self, sys_prompt, user_text):
            nonlocal call_count
            call_count += 1
            return '{"parsed": true}'

    parser = AIParser(api_key="", client=FakeClient())
    result = asyncio.run(parser.parse_email("字节跳动面试邀请"))
    assert result.degraded is True
    assert call_count == 0  # 没调 LLM


# ---------- 4. LLM 成功高置信度 ----------


def test_ai_parser_llm_success():
    """4. LLM 成功且置信度高时 degraded=false。"""

    class FakeClient:
        async def call(self, sys_prompt, user_text):
            return '''{"parsed": true, "company": "字节跳动", "title": "产品经理",
            "suggested_status": "interviewing", "confidence": 0.92,
            "reasoning": "通过笔试邀请面试"}'''

    parser = AIParser(api_key="fake-key", client=FakeClient())
    result = asyncio.run(parser.parse_email("恭喜通过笔试，邀请面试"))
    assert result.parsed is True
    assert result.degraded is False
    assert result.confidence == 0.92
    assert result.company == "字节跳动"


# ---------- 5. LLM 异常降级 ----------


def test_ai_parser_llm_exception_degrades():
    """5. LLM 超时/异常/认证错误时降级正则。"""

    class FailClient:
        async def call(self, sys_prompt, user_text):
            raise ConnectionError("network error")

    parser = AIParser(api_key="fake-key", client=FailClient())
    result = asyncio.run(parser.parse_email("字节跳动面试通知"))
    assert result.degraded is True
    assert result.parsed is True  # 正则成功
    assert result.company == "字节跳动"


# ---------- 6. LLM 非法 JSON / 非法 status / 低置信度降级 ----------


def test_ai_parser_invalid_json_degrades():
    """LLM 返回非法 JSON → 降级。"""

    class BadJSONClient:
        async def call(self, sys, user):
            return "这不是JSON"

    parser = AIParser(api_key="fake-key", client=BadJSONClient())
    result = asyncio.run(parser.parse_email("字节跳动面试"))
    assert result.degraded is True


def test_ai_parser_invalid_status_degrades():
    """LLM 返回非法 status → 降级。"""

    class BadStatusClient:
        async def call(self, sys, user):
            return '{"parsed": true, "suggested_status": "favorited", "confidence": 0.9}'

    parser = AIParser(api_key="fake-key", client=BadStatusClient())
    result = asyncio.run(parser.parse_email("字节跳动"))
    assert result.degraded is True  # 非法 status 触发降级


def test_ai_parser_low_confidence_degrades():
    """LLM 置信度低于阈值 → 降级。"""

    class LowConfClient:
        async def call(self, sys, user):
            return '{"parsed": true, "suggested_status": "interviewing", "confidence": 0.3}'

    parser = AIParser(api_key="fake-key", client=LowConfClient())
    result = asyncio.run(parser.parse_email("字节跳动"))
    assert result.degraded is True  # 低置信度降级


# ---------- 7. TTL cache ----------


def test_cache_hit_no_repeat_llm():
    """7. 缓存命中时不重复调 LLM。"""
    call_count = 0

    class CountingClient:
        async def call(self, sys, user):
            nonlocal call_count
            call_count += 1
            return '{"parsed": true, "company": "字节跳动", "confidence": 0.9}'

    parser = AIParser(api_key="fake-key", client=CountingClient())
    text = "字节跳动面试邀请"
    asyncio.run(parser.parse_email(text))
    asyncio.run(parser.parse_email(text))  # 同文本
    assert call_count == 1  # 只调了一次


# ---------- 8. RateLimiter 超限降级 ----------


def test_rate_limiter_exceeds_degrades():
    """8. 限流超限不调 LLM，直接正则降级。"""
    call_count = 0

    class CountingClient:
        async def call(self, sys, user):
            nonlocal call_count
            call_count += 1
            return '{"parsed": true, "confidence": 0.9}'

    # max_per_minute=1，第二次超限
    clock = [0.0]
    parser = AIParser(api_key="fake-key", client=CountingClient(), max_per_minute=1, clock=lambda: clock[0])
    asyncio.run(parser.parse_email("字节跳动面试一"))
    clock[0] = 10.0  # 不到 60s
    result = asyncio.run(parser.parse_email("腾讯面试二"))
    assert result.degraded is True
    assert call_count == 1  # 第二次没调 LLM


# ---------- 9-10. ApplicationMatcher ----------


@pytest.fixture()
def db_session():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    S = sessionmaker(bind=eng)
    s = S()
    yield s
    s.close()


def test_matcher_unique_match(db_session):
    """9. 归一化精确匹配唯一投递。"""
    db_session.add(Job(company="字节跳动有限公司", title="产品经理", source="manual"))
    db_session.commit()
    job_id = db_session.query(Job).first().id
    db_session.add(Application(job_id=job_id, status=APP_APPLIED))
    db_session.commit()

    matcher = ApplicationMatcher()
    result = matcher.match(db_session, company="字节跳动")  # 归一化后匹配
    assert result is not None


def test_matcher_multiple_unclear_returns_none(db_session):
    """10. 多匹配且岗位不明确 → None。"""
    db_session.add(Job(company="字节跳动", title="产品经理", source="manual"))
    db_session.add(Job(company="字节跳动", title="前端工程师", source="manual"))
    db_session.commit()
    jids = [j.id for j in db_session.query(Job).all()]
    for jid in jids:
        db_session.add(Application(job_id=jid, status=APP_APPLIED))
    db_session.commit()

    matcher = ApplicationMatcher()
    result = matcher.match(db_session, company="字节跳动", title=None)
    assert result is None  # 两个投递，岗位不明确


# ---------- 11-14. API 测试 ----------


@pytest.fixture()
def client(db_session):
    from fastapi.testclient import TestClient
    from src.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_api_parse_email_response_shape(client):
    """11. parse-email 返回完整 response shape。"""
    from src.api.routes.app.applications import set_ai_parser_for_testing

    class FakeLLM:
        async def call(self, sys, user):
            return '{"parsed": true, "company": "字节跳动", "title": "产品经理", "suggested_status": "interviewing", "confidence": 0.92, "reasoning": "面试"}'

    parser = AIParser(api_key="fake", client=FakeLLM())
    set_ai_parser_for_testing(parser)
    try:
        r = client.post("/api/v1/applications/parse-email", json={"email_text": "字节跳动面试邀请"})
        assert r.status_code == 200
        data = r.json()["data"]
        for field in ["parsed", "company", "title", "suggested_status", "confidence", "degraded", "matched_application_id", "reasoning"]:
            assert field in data
    finally:
        set_ai_parser_for_testing(None)


def test_parse_email_no_event_written(client, db_session):
    """12. parse-email 不写 ApplicationEvent，不改 Application.status。"""
    from src.api.routes.app.applications import set_ai_parser_for_testing

    class FakeLLM:
        async def call(self, sys, user):
            return '{"parsed": true, "company": "X", "suggested_status": "interviewing", "confidence": 0.9}'

    parser = AIParser(api_key="fake", client=FakeLLM())
    set_ai_parser_for_testing(parser)

    # 建一个投递
    db_session.add(Job(company="X", title="Y", source="manual"))
    db_session.commit()
    jid = db_session.query(Job).first().id
    db_session.add(Application(job_id=jid, status=APP_APPLIED))
    db_session.commit()
    event_before = db_session.query(ApplicationEvent).count()

    try:
        client.post("/api/v1/applications/parse-email", json={"email_text": "X 面试"})
    finally:
        set_ai_parser_for_testing(None)

    event_after = db_session.query(ApplicationEvent).count()
    assert event_after == event_before  # 没写新事件


def test_api_parse_email_uses_fake_parser(client):
    """13. API 测试用 fake parser，真实 LLM 未被调用。"""
    from src.api.routes.app.applications import set_ai_parser_for_testing

    real_llm_called = [False]

    class TrackingFakeLLM:
        async def call(self, sys, user):
            real_llm_called[0] = True
            return '{"parsed": true, "confidence": 0.9}'

    parser = AIParser(api_key="fake", client=TrackingFakeLLM())
    set_ai_parser_for_testing(parser)
    try:
        client.post("/api/v1/applications/parse-email", json={"email_text": "test"})
        # fake client 被调用了（证明 API 用的是注入的 parser）
        assert real_llm_called[0] is True
    finally:
        set_ai_parser_for_testing(None)


def test_cache_key_not_raw_text():
    """14. 缓存 key 不等于邮件原文（用 hash）。"""
    text = "这是一封包含敏感信息的邮件原文"
    h = text_hash(text)
    assert h != text  # key 是 hash 不是原文
    assert len(h) == 16  # SHA256 前 16 位


def test_parse_email_empty_text_validation(client):
    """空文本返回 VALIDATION_ERROR。"""
    r = client.post("/api/v1/applications/parse-email", json={"email_text": ""})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
