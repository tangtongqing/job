import pytest

from src.crawler.adapters.cmb_campus import (
    CmbCampusAdapter,
    CmbCompletenessError,
)
from src.crawler.adapters.factory import create_adapter
from src.crawler.compliance.robots import RobotsChecker


def _allow_all_robots() -> RobotsChecker:
    return RobotsChecker(fetcher=lambda base_url: "User-agent: *\nAllow: /")


def _job_row(publish_id: str, title: str, location: str = "深圳市") -> dict:
    return {
        "publishGID": publish_id,
        "jobDisplay": title,
        "branchCodeName": "招商银行深圳分行",
        "locationName": location,
        "expiredOn": "2026-09-20",
    }


def _job_detail(row: dict, internship: bool = False) -> dict:
    requirement = (
        "<span>202</span><span>7</span>届在校生，本科及以上学历"
        if internship
        else "<span>202</span><span>7</span>年应届毕业生，本科及以上学历"
    )
    return {
        **row,
        "jobResponsibility": "<p>负责公开招聘岗位相关工作。</p>",
        "jobRequirement": f"<p>{requirement}</p>",
    }


def test_cmb_adapter_exhausts_every_page_and_reconciles_source_total():
    rows_by_type = {
        "full": [
            _job_row("f1", "后端开发工程师"),
            _job_row("f2", "产品经理"),
            _job_row("f3", "风险管理岗", "上海市"),
        ],
        "intern": [_job_row("i1", "市场营销助理实习生")],
    }
    details = {
        row["publishGID"]: _job_detail(row, type_id == "intern")
        for type_id, rows in rows_by_type.items()
        for row in rows
    }
    requests = []

    def requester(method, url, payload):
        requests.append((method, url, dict(payload)))
        if url.endswith("/getList"):
            rows = rows_by_type[payload["recruitmentTypeId"]]
            start = (payload["pageIndex"] - 1) * payload["pageSize"]
            end = start + payload["pageSize"]
            return {
                "returnCode": "SUC0000",
                "body": {"total": len(rows), "data": rows[start:end]},
            }
        publish_id = payload["publishId"]
        return {"returnCode": "SUC0000", "body": details[publish_id]}

    adapter = CmbCampusAdapter(
        config={
            "source_name": "cmb_campus",
            "page_size": 2,
            "min_interval_seconds": 0,
            "recruitment_type_ids": {
                "campus_full_time": "full",
                "internship": "intern",
            },
        },
        robots_checker=_allow_all_robots(),
        json_requester=requester,
    )

    jobs = adapter.crawl()

    assert adapter.source_totals == {
        "campus_full_time": 3,
        "internship": 1,
    }
    assert adapter.source_total == 4
    assert adapter.fetched_total == 4
    assert adapter.parsed_total == 4
    assert {job["external_job_id"] for job in jobs} == {"f1", "f2", "f3", "i1"}
    assert all(job["job_category"] for job in jobs)
    assert all(job["graduation_year"] == "2027" for job in jobs)
    assert next(job for job in jobs if job["external_job_id"] == "i1")[
        "is_intern"
    ] is True

    list_requests = [item for item in requests if item[1].endswith("/getList")]
    assert [item[2]["pageIndex"] for item in list_requests] == [1, 2, 1]
    assert all(item[2]["keywords"] == "" for item in list_requests)
    assert all("max_jobs" not in item[2] for item in list_requests)


def test_cmb_adapter_fails_when_pagination_ends_before_total():
    def requester(method, url, payload):
        page_rows = [_job_row("f1", "开发工程师")] if payload["pageIndex"] == 1 else []
        return {
            "returnCode": "SUC0000",
            "body": {"total": 2, "data": page_rows},
        }

    adapter = CmbCampusAdapter(
        config={
            "source_name": "cmb_campus",
            "page_size": 1,
            "min_interval_seconds": 0,
            "recruitment_type_ids": {"campus_full_time": "full"},
        },
        robots_checker=_allow_all_robots(),
        json_requester=requester,
    )

    with pytest.raises(CmbCompletenessError, match="ended before source total"):
        adapter.fetch()


def test_cmb_adapter_fails_the_whole_crawl_when_one_detail_is_missing():
    row = _job_row("f1", "开发工程师")

    def requester(method, url, payload):
        if url.endswith("/getList"):
            return {
                "returnCode": "SUC0000",
                "body": {"total": 1, "data": [row]},
            }
        return {"returnCode": "SUC0000", "body": {**row}}

    adapter = CmbCampusAdapter(
        config={
            "source_name": "cmb_campus",
            "min_interval_seconds": 0,
            "recruitment_type_ids": {"campus_full_time": "full"},
        },
        robots_checker=_allow_all_robots(),
        json_requester=requester,
    )

    with pytest.raises(CmbCompletenessError, match="parsed 0/1"):
        adapter.crawl()


@pytest.mark.parametrize("forbidden_control", ["keywords", "max_jobs"])
def test_cmb_adapter_rejects_collection_restrictions(forbidden_control):
    with pytest.raises(ValueError, match="does not allow"):
        CmbCampusAdapter(config={forbidden_control: ["product"]})


def test_cmb_adapter_is_registered_in_factory():
    adapter = create_adapter(
        "cmb_campus",
        config={
            "source_name": "cmb_campus",
            "min_interval_seconds": 0,
        },
        robots_checker=_allow_all_robots(),
    )

    assert isinstance(adapter, CmbCampusAdapter)
