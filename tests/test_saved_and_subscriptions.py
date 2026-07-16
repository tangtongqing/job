"""收藏、待投递和订阅闭环契约测试。"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.db.models  # noqa: F401
from src.db.session import Base, get_db
from src.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        session = test_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _job(client, company="星海科技", title="产品经理"):
    response = client.post(
        "/api/v1/jobs",
        json={"company": company, "title": title, "source": "manual"},
    )
    return response.json()["data"]


def test_favorite_lifecycle(client):
    job = _job(client)

    created = client.post(f"/api/v1/jobs/{job['id']}/favorite")
    assert created.status_code == 201
    assert created.json()["data"]["action_type"] == "favorited"

    duplicate = client.post(f"/api/v1/jobs/{job['id']}/favorite")
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CONFLICT"

    listing = client.get("/api/v1/user/favorites")
    assert listing.status_code == 200
    assert listing.json()["meta"]["total"] == 1
    assert listing.json()["data"][0]["job"]["company"] == "星海科技"

    removed = client.delete(f"/api/v1/jobs/{job['id']}/favorite")
    assert removed.status_code == 204
    assert client.get("/api/v1/user/favorites").json()["meta"]["total"] == 0

    # 取消操作幂等，之后也可以重新收藏。
    assert client.delete(f"/api/v1/jobs/{job['id']}/favorite").status_code == 204
    assert client.post(f"/api/v1/jobs/{job['id']}/favorite").status_code == 201


def test_action_requires_existing_job(client):
    response = client.post("/api/v1/jobs/999/favorite")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_creating_application_finishes_to_apply_action(client):
    job = _job(client)
    assert client.post(f"/api/v1/jobs/{job['id']}/to-apply").status_code == 201
    assert client.get("/api/v1/user/to-apply").json()["meta"]["total"] == 1

    application = client.post("/api/v1/applications", json={"job_id": job["id"]})
    assert application.status_code == 201
    assert client.get("/api/v1/user/to-apply").json()["meta"]["total"] == 0


def test_subscription_crud_and_validation(client):
    invalid = client.post(
        "/api/v1/subscriptions",
        json={"keyword": "  ", "company": None, "location": ""},
    )
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"

    created = client.post(
        "/api/v1/subscriptions",
        json={"keyword": " 产品经理 ", "location": "上海"},
    )
    assert created.status_code == 201
    subscription = created.json()["data"]
    assert subscription["keyword"] == "产品经理"

    listing = client.get("/api/v1/subscriptions")
    assert listing.json()["meta"]["total"] == 1

    updated = client.put(
        f"/api/v1/subscriptions/{subscription['id']}",
        json={"company": "字节跳动"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["keyword"] is None
    assert updated.json()["data"]["company"] == "字节跳动"

    assert client.delete(f"/api/v1/subscriptions/{subscription['id']}").status_code == 204
    assert client.get("/api/v1/subscriptions").json()["meta"]["total"] == 0
    missing = client.delete(f"/api/v1/subscriptions/{subscription['id']}")
    assert missing.status_code == 404


def test_demo_reset_is_repeatable_and_restores_full_scenario(client):
    _job(client, company="临时公司", title="重置后应消失")

    first = client.post("/api/v1/demo/reset")
    assert first.status_code == 200
    assert first.json()["data"] == {
        "message": "Demo 数据已重置",
        "jobs": 24,
        "applications": 5,
        "saved_jobs": 4,
        "subscriptions": 3,
    }
    assert client.get("/api/v1/jobs?page_size=100").json()["meta"]["total"] == 24
    assert client.get("/api/v1/user/favorites").json()["meta"]["total"] == 2
    assert client.get("/api/v1/user/to-apply").json()["meta"]["total"] == 2

    second = client.post("/api/v1/demo/reset")
    assert second.status_code == 200
    assert client.get("/api/v1/applications?page_size=100").json()["meta"]["total"] == 5
    assert client.get("/api/v1/subscriptions").json()["meta"]["total"] == 3


def test_demo_reset_creates_schema_for_a_fresh_database():
    """全新数据库不手动跑 init_db，也能直接执行一键重置。"""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db():
        session = test_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).post("/api/v1/demo/reset")
        assert response.status_code == 200
        assert response.json()["data"]["jobs"] == 24
    finally:
        app.dependency_overrides.clear()
