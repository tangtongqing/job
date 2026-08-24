"""Greenhouse public Job Board API adapter.

The endpoint exposes published jobs without authentication.  The adapter uses
the public JSON representation instead of scraping a rendered careers page.
"""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Any, Callable

from bs4 import BeautifulSoup

from src.crawler.adapters.base import BaseAdapter
from src.crawler.compliance.rate_limiter import RateLimiter
from src.crawler.compliance.retry import retry_with_backoff
from src.crawler.normalizer import (
    classify_job,
    extract_education,
    extract_experience,
)


JsonFetcher = Callable[[str], dict[str, Any]]


class GreenhouseAdapter(BaseAdapter):
    """Collect published jobs from one configured Greenhouse board."""

    API_URL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"

    def __init__(
        self,
        config: dict | None = None,
        json_fetcher: JsonFetcher | None = None,
        **_: Any,
    ):
        super().__init__(config)
        self.board_token = str(self.config.get("board_token", "")).strip()
        self.company = str(self.config.get("company", "")).strip()
        self.sample_mode = self.config.get("sample_mode") is True
        sample_controls = {"keywords", "max_jobs"}.intersection(self.config)
        if sample_controls and not self.sample_mode:
            controls = ", ".join(sorted(sample_controls))
            raise ValueError(
                f"Complete collection does not allow {controls}; "
                "set sample_mode=true only for non-production demos"
            )

        configured_max_jobs = self.config.get("max_jobs") if self.sample_mode else None
        self.max_jobs = (
            max(1, int(configured_max_jobs))
            if configured_max_jobs is not None
            else None
        )
        configured_keywords = self.config.get("keywords", []) if self.sample_mode else []
        if isinstance(configured_keywords, str):
            configured_keywords = [configured_keywords]
        self.keywords = [str(item).strip().lower() for item in configured_keywords if str(item).strip()]
        self._json_fetcher = json_fetcher
        self._rate_limiter = RateLimiter(
            min_interval=float(self.config.get("min_interval_seconds", 2))
        )

    def should_crawl(self) -> bool:
        return bool(self.board_token)

    def fetch(self, page: int = 1) -> list[dict]:
        del page  # Greenhouse returns the published board in one public response.
        if not self.board_token:
            return []

        url = self.API_URL.format(token=self.board_token)
        self._rate_limiter.wait_if_needed(self.source_name)
        payload = retry_with_backoff(
            self._fetch_json,
            url,
            max_retries=2,
            base_delay=0.5,
            max_delay=2,
        )
        jobs = payload.get("jobs", [])
        if not isinstance(jobs, list):
            raise ValueError("Greenhouse response does not contain a jobs list")

        if self.keywords:
            jobs = [job for job in jobs if self._matches_keywords(job)]

        jobs.sort(
            key=lambda job: job.get("first_published") or job.get("updated_at") or "",
            reverse=True,
        )
        if self.max_jobs is not None:
            return jobs[: self.max_jobs]
        return jobs

    def _fetch_json(self, url: str) -> dict[str, Any]:
        if self._json_fetcher is not None:
            return self._json_fetcher(url)
        response = self.client.get(url, follow_redirects=True)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Greenhouse response must be a JSON object")
        return payload

    def _matches_keywords(self, job: dict) -> bool:
        departments = " ".join(
            str(item.get("name", ""))
            for item in job.get("departments", [])
            if isinstance(item, dict)
        )
        haystack = f"{job.get('title', '')} {departments}".lower()
        return any(keyword in haystack for keyword in self.keywords)

    def parse(self, raw_data: dict) -> dict | None:
        title = str(raw_data.get("title", "")).strip()
        apply_url = str(raw_data.get("absolute_url", "")).strip()
        if not title or not apply_url:
            return None

        content = html.unescape(str(raw_data.get("content", "")))
        soup = BeautifulSoup(content, "lxml")
        jd = _clean_text(soup.get_text("\n", strip=True))
        if not jd:
            return None

        published_at = _parse_datetime(raw_data.get("first_published"))
        deadline = _parse_datetime(raw_data.get("application_deadline"))
        company = str(self.company or raw_data.get("company_name") or self.board_token).strip()
        location_data = raw_data.get("location") or {}
        location = location_data.get("name") if isinstance(location_data, dict) else None

        return {
            "company": company,
            "title": title,
            "location": str(location).strip() if location else None,
            "salary": _extract_salary(jd),
            "jd": jd,
            "requirement": _extract_requirements(jd),
            "apply_url": apply_url,
            "source_url": apply_url,
            "job_category": classify_job(title, jd),
            "education": extract_education(jd),
            "experience": extract_experience(jd),
            "published_at": published_at,
            "deadline": deadline,
            "is_intern": "intern" in title.lower(),
            "is_fresh": bool(
                published_at
                and (
                    datetime.now(timezone.utc).replace(tzinfo=None) - published_at
                ).days
                <= 14
            ),
        }


def _clean_text(value: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except ValueError:
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d")
        except ValueError:
            return None


def _extract_requirements(text: str) -> str | None:
    starts = {
        "requirements",
        "qualifications",
        "what you'll bring",
        "what you’ll bring",
        "what you bring",
        "who you are",
        "about you",
        "minimum requirements",
        "what we look for",
        "we'd love to hear from you if",
        "we'd love to hear from you if you have",
        "we’d love to hear from you if you have",
        "must have experience",
        "what skills do i need?",
    }
    ends = {
        "benefits",
        "compensation",
        "pay range",
        "salary range",
        "about us",
        "equal opportunity",
        "why you should apply",
        "why this role, why now",
        "additional information",
        "what you'll be doing",
        "what you’ll be doing",
        "what success looks like",
        "interview process",
        "pay transparency disclosure",
        "equal opportunity workplace",
    }
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    def heading(line: str) -> str:
        return line.lower().strip().rstrip(":")

    start_indexes = [index for index, line in enumerate(lines) if heading(line) in starts]
    if not start_indexes:
        return None
    start = min(start_indexes)
    end_indexes = [
        index
        for index, line in enumerate(lines[start + 1 :], start=start + 1)
        if heading(line) in ends
    ]
    end = min(end_indexes) if end_indexes else len(lines)
    result = "\n".join(lines[start:end]).strip()
    return result[:4000] or None


_SALARY_PATTERNS = [
    re.compile(r"[$£€]\s?\d{2,3}(?:,\d{3})?\s*(?:-|to|–|—)\s*[$£€]?\s?\d{2,3}(?:,\d{3})?(?:\s*(?:a year|per year|annually))?", re.I),
    re.compile(r"\d{2,3}(?:,\d{3})?\s*(?:-|to|–|—)\s*\d{2,3}(?:,\d{3})?\s*(?:USD|GBP|EUR)", re.I),
]


def _extract_salary(text: str) -> str | None:
    for pattern in _SALARY_PATTERNS:
        match = pattern.search(text)
        if match:
            return re.sub(r"\s+", " ", match.group(0)).strip()
    return None
