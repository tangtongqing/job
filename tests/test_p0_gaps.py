"""公开情景走查发现的两个 P0 闭环缺口回归测试。"""

from datetime import datetime, timedelta

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


def _create_application(client: TestClient) -> dict:
    job_response = client.post(
        "/api/v1/jobs",
        json={"company": "MiniMax", "title": "AI 产品经理", "source": "manual"},
    )
    job_id = job_response.json()["data"]["id"]
    return client.post(
        "/api/v1/applications",
        json={"job_id": job_id},
    ).json()["data"]


def test_confirmed_interview_time_creates_todo_and_timeline_event(client):
    application = _create_application(client)
    scheduled_at = (datetime.utcnow() + timedelta(days=3)).replace(
        hour=10,
        minute=30,
        second=0,
        microsecond=0,
    )

    response = client.post(
        f"/api/v1/applications/{application['id']}/transition",
        json={
            "to_status": "interviewing",
            "scheduled_at": scheduled_at.isoformat(),
            "scheduled_event_type": "interview",
            "round": 1,
            "note": "由招聘通知确认",
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["event"]["event_type"] == "status_change"
    assert data["event"]["to_status"] == "interviewing"
    assert data["scheduled_event"]["event_type"] == "interview"
    assert data["scheduled_event"]["scheduled_at"] == scheduled_at.isoformat()
    assert data["scheduled_event"]["occurred_at"] is None

    todo_response = client.get("/api/v1/todo?days=7")
    assert todo_response.status_code == 200
    todos = todo_response.json()["data"]
    assert len(todos) == 1
    assert todos[0]["application_id"] == application["id"]
    assert todos[0]["event_type"] == "interview"
    assert todos[0]["job"]["company"] == "MiniMax"

    detail = client.get(
        f"/api/v1/applications/{application['id']}"
    ).json()["data"]
    assert any(
        event["event_type"] == "interview"
        and event["scheduled_at"] == scheduled_at.isoformat()
        for event in detail["events"]
    )


def test_schedule_type_must_match_target_status(client):
    application = _create_application(client)
    scheduled_at = datetime.utcnow() + timedelta(days=2)

    response = client.post(
        f"/api/v1/applications/{application['id']}/transition",
        json={
            "to_status": "interviewing",
            "scheduled_at": scheduled_at.isoformat(),
            "scheduled_event_type": "test",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    detail = client.get(
        f"/api/v1/applications/{application['id']}"
    ).json()["data"]
    assert detail["status"] == "applied"
    assert len(detail["events"]) == 1


def test_schedule_write_failure_rolls_back_status_transition(client, monkeypatch):
    """附加计划事件失败时，状态事件也不能单独落库。"""
    from src.api.routes.app import applications as application_routes

    application = _create_application(client)

    def fail_to_add_schedule(*args, **kwargs):
        raise RuntimeError("simulated schedule write failure")

    monkeypatch.setattr(application_routes, "add_interview", fail_to_add_schedule)

    with pytest.raises(RuntimeError, match="simulated schedule write failure"):
        client.post(
            f"/api/v1/applications/{application['id']}/transition",
            json={
                "to_status": "interviewing",
                "scheduled_at": (
                    datetime.utcnow() + timedelta(days=2)
                ).isoformat(),
                "scheduled_event_type": "interview",
            },
        )

    detail = client.get(
        f"/api/v1/applications/{application['id']}"
    ).json()["data"]
    assert detail["status"] == "applied"
    assert len(detail["events"]) == 1


def test_manual_external_application_creates_complete_record(client):
    payload = {
        "company": "Notion",
        "title": "Product Manager",
        "location": "Remote",
        "source_url": "https://example.com/jobs/notion-pm",
        "applied_at": "2026-07-20T12:00:00",
        "notes": "官网投递，使用产品版简历",
    }

    response = client.post("/api/v1/applications/manual", json=payload)

    assert response.status_code == 201
    created = response.json()["data"]
    assert created["status"] == "applied"
    assert created["applied_at"] == payload["applied_at"]

    detail = client.get(
        f"/api/v1/applications/{created['id']}"
    ).json()["data"]
    assert detail["job"]["company"] == "Notion"
    assert detail["job"]["title"] == "Product Manager"
    assert detail["job"]["source"] == "manual"
    assert detail["job"]["apply_url"] == payload["source_url"]
    assert detail["job"]["source_url"] == payload["source_url"]
    assert detail["notes"] == payload["notes"]
    assert len(detail["events"]) == 1
    assert detail["events"][0]["to_status"] == "applied"
    assert detail["events"][0]["occurred_at"] == payload["applied_at"]

    listed = client.get(
        "/api/v1/applications?page_size=100"
    ).json()["data"]
    assert any(
        item["id"] == created["id"]
        and item["job"]["company"] == "Notion"
        for item in listed
    )


def test_manual_external_application_rejects_duplicate_active_record(client):
    payload = {
        "company": "Notion",
        "title": "Product Manager",
        "location": "Remote",
    }
    first = client.post("/api/v1/applications/manual", json=payload)
    second = client.post("/api/v1/applications/manual", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "CONFLICT"


def test_manual_external_application_validates_source_url(client):
    response = client.post(
        "/api/v1/applications/manual",
        json={
            "company": "Notion",
            "title": "Product Manager",
            "source_url": "not-a-url",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
