import json
from pathlib import Path

import pytest

from src.crawler.source_registry import (
    SourceRegistryError,
    load_company_source_registry,
)
from src.api.responses import ValidationError
from src.crawler.config import (
    CrawlerConfig,
    CrawlerGlobalConfig,
    CrawlerSourceConfig,
)
from src.crawler.service import CrawlService


EXPECTED_COMPANIES = {
    "tencent",
    "bytedance",
    "alibaba",
    "meituan",
    "huawei",
    "dji",
    "byd",
    "cmb",
    "china_mobile",
    "midea",
}


def test_pilot_registry_contains_ten_reviewed_companies():
    registry = load_company_source_registry()

    assert {company.id for company in registry.companies} == EXPECTED_COMPANIES
    assert set(registry.collection_scope) == {
        "campus_full_time",
        "graduate_program",
        "internship",
    }
    assert registry.enabled_sources() == ()


def test_registry_keeps_restricted_sources_disabled():
    registry = load_company_source_registry()

    tencent = registry.get_source("tencent_campus")
    assert tencent is not None
    assert tencent.automation_decision == "prohibited"
    assert tencent.status == "paused"
    assert tencent.enabled is False


def test_registry_connects_cmb_to_complete_adapter():
    registry = load_company_source_registry()

    cmb = registry.get_source("cmb_campus")
    assert cmb is not None
    assert cmb.adapter == "cmb_campus"
    assert cmb.collection_mode == "complete"
    assert set(cmb.adapter_options["recruitment_type_ids"]) == {
        "campus_full_time",
        "internship",
    }


@pytest.mark.parametrize("forbidden_option", ["keywords", "max_jobs"])
def test_registry_rejects_complete_sources_with_silent_limits(
    tmp_path,
    forbidden_option,
):
    path = tmp_path / "registry.json"
    raw = {
        "schema_version": 1,
        "updated_at": "2026-08-05",
        "collection_scope": [
            "campus_full_time",
            "graduate_program",
            "internship",
        ],
        "companies": [
            {
                "id": "example",
                "name": "示例公司",
                "aliases": [],
                "industry": "测试",
                "priority": 1,
                "official_domains": ["careers.example.com"],
                "sources": [
                    {
                        "id": "example_campus",
                        "source_type": "official_career_site",
                        "canonical_url": "https://careers.example.com/campus",
                        "job_list_url": "https://careers.example.com/jobs",
                        "adapter": "example",
                        "adapter_options": {forbidden_option: ["product"]},
                        "collection_mode": "complete",
                        "enabled": False,
                        "status": "reviewing",
                        "automation_decision": "pending",
                        "robots_status": "pending",
                        "terms_status": "pending",
                        "last_reviewed_at": "2026-08-05",
                        "evidence_urls": [],
                        "notes": ""
                    }
                ]
            }
        ]
    }
    path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(SourceRegistryError, match="collection restrictions"):
        load_company_source_registry(path)


def test_registry_rejects_enabled_source_without_allowed_decision(tmp_path):
    path = tmp_path / "registry.json"
    raw = json.loads(
        Path("config/company_sources.json").read_text(encoding="utf-8")
    )
    raw["companies"][1]["sources"][0]["enabled"] = True
    raw["companies"][1]["sources"][0]["status"] = "enabled"
    path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(SourceRegistryError, match="enabled without an allowed"):
        load_company_source_registry(path)


def test_runtime_cannot_enable_source_while_registry_review_is_pending():
    registry = load_company_source_registry()
    config = CrawlerConfig(
        global_config=CrawlerGlobalConfig(),
        sources={
            "cmb_campus": CrawlerSourceConfig(
                name="cmb_campus",
                adapter="cmb_campus",
                enabled=True,
                options={"registry_source_id": "cmb_campus"},
            )
        },
    )
    service = CrawlService(config=config, source_registry=registry)

    with pytest.raises(ValidationError, match="尚未批准自动采集"):
        service.crawl_source(None, "cmb_campus")
