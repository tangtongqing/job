from pathlib import Path

from fastapi.testclient import TestClient

from src.config import Settings, get_settings
from src.main import app


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_sites_layout_does_not_embed_local_next_font_paths():
    layout_source = (PROJECT_ROOT / "web" / "app" / "layout.tsx").read_text(
        encoding="utf-8"
    )

    assert "next/font" not in layout_source


def test_subscription_form_has_inline_empty_condition_validation():
    page_source = (
        PROJECT_ROOT / "web" / "app" / "(app)" / "subscriptions" / "page.tsx"
    ).read_text(encoding="utf-8")

    assert 'role="alert"' in page_source
    assert "至少填写关键词、公司或地点中的一项" in page_source


def test_favorite_card_reflects_existing_to_apply_state():
    page_source = (
        PROJECT_ROOT / "web" / "app" / "(app)" / "saved" / "page.tsx"
    ).read_text(encoding="utf-8")

    assert "toApplyJobIds" in page_source
    assert "查看待投递" in page_source


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
