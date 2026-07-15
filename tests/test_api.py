"""API 层契约测试（返工002 要求的 13 项 + 核心闭环）。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.session import Base, get_db
import src.db.models  # noqa
from src.main import app


@pytest.fixture()
def client():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    TestSession = sessionmaker(bind=eng, autocommit=False, autoflush=False)

    def override_get_db():
        s = TestSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _job(client, **kw):
    payload = {"company": "测试公司", "title": "产品经理", "source": "manual"}
    payload.update(kw)
    return client.post("/api/v1/jobs", json=payload).json()["data"]


def _app(client, job_id):
    return client.post("/api/v1/applications", json={"job_id": job_id}).json()["data"]


# ========== 1. distribution 200 + 结构 ==========


def test_distribution_returns_200_with_contract(client):
    """1. distribution 不再 500，返回 {dimension, distribution, total}。"""
    j = _job(client, job_category="product")
    _app(client, j["id"])  # 建投递让 distribution 有数据
    r = client.get("/api/v1/dashboard/distribution?dimension=job_category")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "dimension" in data
    assert "distribution" in data
    assert "total" in data
    assert any(item["label"] == "product" for item in data["distribution"])


def test_distribution_invalid_dimension_validation_error(client):
    """非法 dimension 返回 VALIDATION_ERROR。"""
    r = client.get("/api/v1/dashboard/distribution?dimension=bad_dim")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# ========== 2. kpi 契约字段 ==========


def test_kpi_contract_fields(client):
    """2. kpi 含 today_new_jobs/total_jobs/total_applications/pending_applications/by_status。"""
    r = client.get("/api/v1/dashboard/kpi")
    assert r.status_code == 200
    data = r.json()["data"]
    for field in ["today_new_jobs", "total_jobs", "total_applications", "pending_applications", "by_status"]:
        assert field in data, f"缺字段 {field}"


# ========== 3. funnel 含 applied 初始事件 ==========


def test_funnel_contract_and_initial_event(client):
    """3. funnel 含 funnel/total_applications，含 applied。"""
    j = _job(client)
    _app(client, j["id"])  # 创建投递会写 applied 初始事件
    r = client.get("/api/v1/dashboard/funnel")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "funnel" in data
    assert "total_applications" in data
    statuses = [item["status"] for item in data["funnel"]]
    assert "applied" in statuses


def test_funnel_counts_reached_stages_from_events(client):
    """进入后续阶段后，漏斗仍应累计 applied/test/interviewing 到达数。"""
    j = _job(client)
    a = _app(client, j["id"])
    client.post(f"/api/v1/applications/{a['id']}/transition", json={"to_status": "test"})
    client.post(
        f"/api/v1/applications/{a['id']}/transition",
        json={"to_status": "interviewing"},
    )

    r = client.get("/api/v1/dashboard/funnel")
    assert r.status_code == 200
    counts = {item["status"]: item["count"] for item in r.json()["data"]["funnel"]}
    assert counts["applied"] == 1
    assert counts["test"] == 1
    assert counts["interviewing"] == 1


# ========== 4. trend 统计有效进展事件 ==========


def test_trend_counts_progress_events(client):
    """4. trend 统计 test/interviewing/offer_pending 事件，不统计 applied_at。"""
    j = _job(client)
    a = _app(client, j["id"])
    # 流转到 test（应产生进展事件）
    client.post(f"/api/v1/applications/{a['id']}/transition", json={"to_status": "test"})
    r = client.get("/api/v1/dashboard/trend?days=7")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "trend" in data
    assert "total" in data
    assert data["total"] >= 1  # 至少1个进展事件


def test_trend_days_returns_exact_number_of_points(client):
    """days=N 时返回正好 N 个日期点。"""
    r1 = client.get("/api/v1/dashboard/trend?days=1")
    r7 = client.get("/api/v1/dashboard/trend?days=7")
    assert r1.status_code == 200
    assert r7.status_code == 200
    assert len(r1.json()["data"]["trend"]) == 1
    assert len(r7.json()["data"]["trend"]) == 7


# ========== 5. 参数校验返回 {error.code=VALIDATION_ERROR} ==========


def test_validation_error_envelope(client):
    """5. GET /jobs?page=bad 返回 {error.code=VALIDATION_ERROR}。"""
    r = client.get("/api/v1/jobs?page=bad")
    assert r.status_code == 400
    body = r.json()
    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_body_validation_error_envelope(client):
    """缺失必填 body 字段也返回 {error}。"""
    r = client.post("/api/v1/jobs", json={})  # 缺 company/title
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# ========== 6. to_status=favorited 返回 VALIDATION_ERROR ==========


def test_invalid_to_status_enum(client):
    """6. to_status=favorited 是 VALIDATION_ERROR（枚举校验）。"""
    j = _job(client)
    a = _app(client, j["id"])
    r = client.post(
        f"/api/v1/applications/{a['id']}/transition",
        json={"to_status": "favorited"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# ========== 7. 合法状态但非法流转返回 INVALID_TRANSITION ==========


def test_invalid_transition_code(client):
    """7. offer_accepted→interviewing（非纠错）是 INVALID_TRANSITION。"""
    j = _job(client)
    a = _app(client, j["id"])
    # 流到 offer_accepted
    for to in ["interviewing", "offer_pending", "offer_accepted"]:
        client.post(f"/api/v1/applications/{a['id']}/transition", json={"to_status": to})
    # 终态→非终态 非纠错
    r = client.post(
        f"/api/v1/applications/{a['id']}/transition",
        json={"to_status": "interviewing"},
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_TRANSITION"


# ========== 8. batch-transition 契约字段 + 部分失败不中断 ==========


def test_batch_transition_contract(client):
    """8. batch 返回 succeeded/failed/total/success_count/fail_count。"""
    j1 = _job(client, company="c1")
    j2 = _job(client, company="c2")
    a1 = _app(client, j1["id"])
    a2 = _app(client, j2["id"])
    # a1 流到终态，再批量流转会失败（终态不可常规流转）
    for to in ["interviewing", "offer_pending", "offer_accepted"]:
        client.post(f"/api/v1/applications/{a1['id']}/transition", json={"to_status": to})

    r = client.post(
        "/api/v1/applications/batch-transition",
        json={"application_ids": [a1["id"], a2["id"]], "to_status": "test"},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert "succeeded" in data
    assert "failed" in data
    assert data["total"] == 2
    assert data["success_count"] + data["fail_count"] == 2
    # a2 应成功，a1 应失败
    assert a2["id"] in data["succeeded"]
    assert any(f["application_id"] == a1["id"] for f in data["failed"])
    assert data["failed"][0]["error_code"] == "INVALID_TRANSITION"


# ========== 9. application 详情含 events ==========


def test_application_detail_includes_events(client):
    """9. GET /applications/{id} 含 events 时间线。"""
    j = _job(client)
    a = _app(client, j["id"])
    client.post(f"/api/v1/applications/{a['id']}/transition", json={"to_status": "test"})

    r = client.get(f"/api/v1/applications/{a['id']}")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "events" in data
    assert len(data["events"]) >= 2  # 初始 applied + test
    assert "job" in data


# ========== 10. transition 响应含 event ==========


def test_transition_returns_event(client):
    """10. POST transition 响应含本次 event。"""
    j = _job(client)
    a = _app(client, j["id"])
    r = client.post(
        f"/api/v1/applications/{a['id']}/transition",
        json={"to_status": "test"},
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert "application" in data
    assert "event" in data
    assert data["event"]["to_status"] == "test"
    assert data["event"]["event_type"] == "status_change"


# ========== 11. todo 含 event_id/job/days_left/round ==========


def test_todo_contract_fields(client):
    """11. todo item 含 event_id/job/days_left/round。"""
    from datetime import datetime, timedelta
    from src.core.events import add_interview

    j = _job(client)
    a = _app(client, j["id"])

    # 通过 fixture 的同一 session 建未来待办（拿 override 后的 session）
    db_gen = app.dependency_overrides[get_db]()
    s = next(db_gen)
    add_interview(
        s, a["id"],
        round=1,
        scheduled_at=datetime.utcnow() + timedelta(days=3),
    )
    s.commit()

    r = client.get("/api/v1/todo?days=7")
    assert r.status_code == 200
    todos = r.json()["data"]
    assert len(todos) == 1
    t = todos[0]
    assert "event_id" in t
    assert "job" in t
    assert "days_left" in t
    assert "round" in t
    assert t["job"]["company"] == "测试公司"


# ========== 12. jobs stats 契约字段 ==========


def test_jobs_stats_contract(client):
    """12. /jobs/stats 含 today_new/total/valid/invalid。"""
    _job(client)
    r = client.get("/api/v1/jobs/stats")
    assert r.status_code == 200
    data = r.json()["data"]
    for field in ["today_new", "total", "valid", "invalid"]:
        assert field in data, f"缺字段 {field}"


# ========== 13. JobOut 含 last_verified_at ==========


def test_jobout_has_last_verified_at(client):
    """13. JobOut 响应含 last_verified_at。"""
    j = _job(client)
    r = client.get(f"/api/v1/jobs/{j['id']}")
    assert "last_verified_at" in r.json()["data"]


# ========== 14. GET /applications 列表含 job 摘要 + 无 N+1 ==========


def test_applications_list_has_job_summary(client):
    """列表返回 job 摘要（company/title），不只是 job_id。"""
    j = _job(client, company="字节跳动", title="产品经理")
    _app(client, j["id"])
    r = client.get("/api/v1/applications")
    assert r.status_code == 200
    item = r.json()["data"][0]
    assert item["job"] is not None
    assert item["job"]["company"] == "字节跳动"
    assert item["job"]["title"] == "产品经理"


def test_applications_list_no_n1_events_query(client):
    """列表不触发 per-application events 懒加载（QA-REWORK-002 回归）。

    用 SQLAlchemy before_cursor_execute 事件计数 application_event 表查询次数。
    3 个投递 + 列表请求 → application_event 查询应为 0（列表不加载 events）。
    """
    from sqlalchemy import event as sa_event

    # 建 3 个投递
    for i in range(3):
        j = _job(client, company=f"c{i}", title=f"t{i}")
        _app(client, j["id"])

    # 拿 fixture 的 engine
    from src.main import app as _app_obj
    db_gen = _app_obj.dependency_overrides[get_db]()
    s = next(db_gen)
    eng = s.bind

    event_query_count = [0]

    @sa_event.listens_for(eng, "before_cursor_execute")
    def count_event_queries(conn, cursor, statement, params, context, executemany):
        if "application_event" in statement.lower():
            event_query_count[0] += 1

    try:
        r = client.get("/api/v1/applications")
        assert r.status_code == 200
        # 列表请求期间，application_event 表查询应为 0（不懒加载 events）
        assert event_query_count[0] == 0, (
            f"列表触发了 {event_query_count[0]} 次 application_event 查询，存在 N+1"
        )
    finally:
        sa_event.remove(eng, "before_cursor_execute", count_event_queries)
