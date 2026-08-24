"""招商银行官方校园招聘公开接口适配器。

该适配器只调用官网正常浏览时使用的公开列表与详情接口，不登录、
不提交简历，也不模拟或绕过任何客户端签名。正式调度仍由来源注册表
和 ``sources.yaml`` 的合规状态共同控制。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from bs4 import BeautifulSoup

from src.crawler.adapters.base import BaseAdapter
from src.crawler.compliance.rate_limiter import RateLimiter
from src.crawler.compliance.retry import retry_with_backoff
from src.crawler.compliance.robots import RobotsChecker
from src.crawler.normalizer import (
    classify_job,
    extract_education,
    extract_graduation_year,
)


JsonRequester = Callable[[str, str, dict[str, Any]], dict[str, Any]]


class CmbCompletenessError(ValueError):
    """Raised when the source total cannot be reconciled with fetched rows."""


class CmbCampusAdapter(BaseAdapter):
    """Collect every published CMB graduate and internship position."""

    CAMPUS_URL = "https://career.cmbchina.com/campus/home"
    LIST_URL = (
        "https://career.cmbchina.com/api/"
        "campusRecruitmentWebsite/job/getList"
    )
    DETAIL_URL = (
        "https://career.cmbchina.com/api/"
        "campusRecruitmentWebsite/job/getDetail"
    )
    DETAIL_PAGE_URL = (
        "https://career.cmbchina.com/positionDetail/school?publishId={publish_id}"
    )
    DEFAULT_RECRUITMENT_TYPE_IDS = {
        "campus_full_time": "96574F8D-C7ED-4772-AE7C-BAC896D190C1",
        "internship": "DF94FD6D-26D3-4A19-9E69-577C4BA1DE82",
    }

    def __init__(
        self,
        config: dict | None = None,
        robots_checker: RobotsChecker | None = None,
        json_requester: JsonRequester | None = None,
        **_: Any,
    ):
        super().__init__(config)
        forbidden_controls = {"keywords", "max_jobs"}.intersection(self.config)
        if forbidden_controls:
            controls = ", ".join(sorted(forbidden_controls))
            raise ValueError(
                f"Complete campus collection does not allow {controls}"
            )

        configured_types = self.config.get("recruitment_type_ids")
        if configured_types is None:
            configured_types = self.DEFAULT_RECRUITMENT_TYPE_IDS
        if not isinstance(configured_types, dict) or not configured_types:
            raise ValueError("recruitment_type_ids must be a non-empty mapping")
        self.recruitment_type_ids = {
            str(kind).strip(): str(type_id).strip()
            for kind, type_id in configured_types.items()
            if str(kind).strip() and str(type_id).strip()
        }
        if not self.recruitment_type_ids:
            raise ValueError("recruitment_type_ids contains no valid entries")

        self.company = str(self.config.get("company", "招商银行")).strip()
        self.page_size = max(1, min(int(self.config.get("page_size", 50)), 100))
        self.robots_checker = robots_checker or RobotsChecker()
        self._json_requester = json_requester
        self._rate_limiter = RateLimiter(
            min_interval=float(self.config.get("min_interval_seconds", 1))
        )

        self.source_total = 0
        self.fetched_total = 0
        self.parsed_total = 0
        self.source_totals: dict[str, int] = {}

    def should_crawl(self) -> bool:
        return self.robots_checker.can_fetch(self.CAMPUS_URL)

    def fetch(self, page: int = 1) -> list[dict]:
        if page != 1:
            raise ValueError("CMB adapter manages complete pagination internally")

        all_rows: list[dict] = []
        source_totals: dict[str, int] = {}

        for recruitment_kind, recruitment_type_id in self.recruitment_type_ids.items():
            rows = self._fetch_recruitment_type(
                recruitment_kind,
                recruitment_type_id,
            )
            source_totals[recruitment_kind] = len(rows)
            all_rows.extend(rows)

        self.source_totals = source_totals
        self.source_total = sum(source_totals.values())
        self.fetched_total = len(all_rows)
        if self.fetched_total != self.source_total:
            raise CmbCompletenessError(
                "CMB source totals do not reconcile with fetched rows"
            )
        return all_rows

    def _fetch_recruitment_type(
        self,
        recruitment_kind: str,
        recruitment_type_id: str,
    ) -> list[dict]:
        page_index = 1
        expected_total: int | None = None
        rows: list[dict] = []
        seen_ids: set[str] = set()

        while expected_total is None or len(rows) < expected_total:
            payload = {
                "orgIdList": [],
                "keywords": "",
                "locationIdList": [],
                "pageIndex": page_index,
                "pageSize": self.page_size,
                "recruitmentTypeId": recruitment_type_id,
                "jobTypeIdList": [],
            }
            response = self._request_json("POST", self.LIST_URL, payload)
            body = self._response_body(response, "job list")

            try:
                page_total = int(body.get("total", 0))
            except (TypeError, ValueError) as exc:
                raise CmbCompletenessError(
                    f"Invalid CMB source total for {recruitment_kind}"
                ) from exc

            if expected_total is None:
                expected_total = page_total
            elif page_total != expected_total:
                raise CmbCompletenessError(
                    f"CMB source total changed during pagination for "
                    f"{recruitment_kind}: {expected_total} -> {page_total}"
                )

            page_rows = body.get("data", [])
            if not isinstance(page_rows, list):
                raise CmbCompletenessError("CMB job list data must be an array")
            if not page_rows and len(rows) < expected_total:
                raise CmbCompletenessError(
                    f"CMB pagination ended before source total for "
                    f"{recruitment_kind}: {len(rows)}/{expected_total}"
                )

            for row in page_rows:
                if not isinstance(row, dict):
                    raise CmbCompletenessError("CMB job row must be an object")
                publish_id = str(row.get("publishGID", "")).strip()
                if not publish_id:
                    raise CmbCompletenessError("CMB job row has no publishGID")
                if publish_id in seen_ids:
                    raise CmbCompletenessError(
                        f"CMB pagination returned duplicate publishGID: {publish_id}"
                    )
                seen_ids.add(publish_id)
                rows.append(
                    {
                        **row,
                        "_recruitment_kind": recruitment_kind,
                        "_recruitment_type_id": recruitment_type_id,
                    }
                )

            if len(rows) > expected_total:
                raise CmbCompletenessError(
                    f"CMB fetched more rows than source total for "
                    f"{recruitment_kind}: {len(rows)}/{expected_total}"
                )
            page_index += 1

        if len(rows) != expected_total:
            raise CmbCompletenessError(
                f"CMB source total mismatch for {recruitment_kind}: "
                f"{len(rows)}/{expected_total}"
            )
        return rows

    def parse(self, raw_data: dict) -> dict | None:
        publish_id = str(raw_data.get("publishGID", "")).strip()
        if not publish_id:
            return None

        response = self._request_json(
            "GET",
            self.DETAIL_URL,
            {"publishId": publish_id},
        )
        detail = self._response_body(response, "job detail")

        title = str(
            detail.get("jobDisplay") or raw_data.get("jobDisplay") or ""
        ).strip()
        if not title:
            return None

        responsibility = _html_to_text(detail.get("jobResponsibility"))
        requirement = _html_to_text(detail.get("jobRequirement"))
        if not responsibility and not requirement:
            return None

        location = str(
            detail.get("locationName") or raw_data.get("locationName") or ""
        ).strip()
        branch_name = str(
            detail.get("branchCodeName")
            or raw_data.get("branchCodeName")
            or self.company
        ).strip()
        recruitment_kind = str(
            raw_data.get("_recruitment_kind", "campus_full_time")
        )
        apply_url = self.DETAIL_PAGE_URL.format(publish_id=publish_id)

        return {
            "external_job_id": publish_id,
            "company": branch_name,
            "parent_company": self.company,
            "title": title,
            "location": location or None,
            "jd": responsibility or requirement,
            "requirement": requirement or None,
            "apply_url": apply_url,
            "source_url": apply_url,
            "job_category": classify_job(title, responsibility) or "other",
            "graduation_year_raw": requirement,
            "graduation_year": extract_graduation_year(requirement),
            "education_raw": requirement,
            "education": extract_education(requirement),
            "experience_raw": requirement,
            "deadline": _parse_date(
                detail.get("expiredOn") or raw_data.get("expiredOn")
            ),
            "is_intern": recruitment_kind == "internship",
            "is_fresh": recruitment_kind == "campus_full_time",
            "employment_type": recruitment_kind,
            "authority_level": "official",
        }

    def crawl(self) -> list[dict]:
        if not self.should_crawl():
            return []

        raw_rows = self.fetch()
        parsed_rows: list[dict] = []
        failed_ids: list[str] = []
        for raw_row in raw_rows:
            try:
                parsed = self.parse(raw_row)
            except Exception:
                failed_ids.append(str(raw_row.get("publishGID", "unknown")))
                continue
            if parsed is None:
                failed_ids.append(str(raw_row.get("publishGID", "unknown")))
            else:
                parsed_rows.append(parsed)

        self.parsed_total = len(parsed_rows)
        if failed_ids or self.parsed_total != self.fetched_total:
            preview = ", ".join(failed_ids[:5])
            raise CmbCompletenessError(
                f"CMB parsed {self.parsed_total}/{self.fetched_total} jobs; "
                f"failed publishGID: {preview}"
            )
        return parsed_rows

    def _request_json(
        self,
        method: str,
        url: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        self._rate_limiter.wait_if_needed(self.source_name)
        response = retry_with_backoff(
            self._perform_request,
            method,
            url,
            payload,
            max_retries=2,
            base_delay=0.5,
            max_delay=2,
        )
        if not isinstance(response, dict):
            raise ValueError("CMB response must be a JSON object")
        return response

    def _perform_request(
        self,
        method: str,
        url: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if self._json_requester is not None:
            return self._json_requester(method, url, payload)

        if method == "POST":
            response = self.client.post(url, json=payload)
        elif method == "GET":
            response = self.client.get(url, params=payload)
        else:
            raise ValueError(f"Unsupported CMB request method: {method}")
        response.raise_for_status()
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError("CMB response must be a JSON object")
        return result

    @staticmethod
    def _response_body(response: dict[str, Any], context: str) -> dict[str, Any]:
        if response.get("returnCode") != "SUC0000":
            raise ValueError(
                f"CMB {context} failed: "
                f"{response.get('returnCode')} {response.get('errorMsg')}"
            )
        body = response.get("body")
        if not isinstance(body, dict):
            raise ValueError(f"CMB {context} response has no body")
        return body


def _html_to_text(value: Any) -> str:
    if not value:
        return ""
    soup = BeautifulSoup(str(value), "lxml")
    blocks = soup.find_all(["p", "li"])
    if blocks:
        return "\n".join(
            text
            for block in blocks
            if (text := block.get_text("", strip=True))
        )
    return soup.get_text(" ", strip=True)


def _parse_date(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
