from fastapi.testclient import TestClient

from src.config import Settings, get_settings
from src.main import app


def test_cors_origins_are_normalized_from_csv():
    settings = Settings(cors_origins="https://demo.example.com/, http://localhost:3100, ")

    assert settings.allowed_cors_origins == [
        "https://demo.example.com",
        "http://localhost:3100",
    ]


def test_public_demo_can_disable_crawler_trigger(monkeypatch):
    monkeypatch.setenv("CRAWLER_TRIGGER_ENABLED", "false")
    get_settings.cache_clear()
    try:
        response = TestClient(app).post(
            "/api/v1/crawler/trigger", json={"source": "company"}
        )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"
