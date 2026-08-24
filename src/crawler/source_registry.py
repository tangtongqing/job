"""Version-controlled registry for official campus recruitment sources.

The registry is deliberately separate from ``sources.yaml``: a source must be
reviewed here before it can be copied into the runtime scheduler config.  This
keeps discovery from silently becoming permission to crawl.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_SOURCE_REGISTRY_PATH = Path("config/company_sources.json")

_SOURCE_STATUSES = {
    "candidate",
    "reviewing",
    "approved",
    "enabled",
    "degraded",
    "paused",
    "rejected",
    "retired",
}
_AUTOMATION_DECISIONS = {"allowed", "pending", "prohibited"}
_REQUIRED_SCOPE = {"campus_full_time", "graduate_program", "internship"}
_FORBIDDEN_COMPLETE_OPTIONS = {"keywords", "max_jobs"}


class SourceRegistryError(ValueError):
    """Raised when the official source registry violates a safety invariant."""


@dataclass(frozen=True)
class RegisteredSource:
    id: str
    company_id: str
    source_type: str
    canonical_url: str
    job_list_url: str
    adapter: str
    adapter_options: dict[str, Any]
    collection_mode: str
    enabled: bool
    status: str
    automation_decision: str
    robots_status: str
    terms_status: str
    last_reviewed_at: str
    evidence_urls: tuple[str, ...]
    notes: str


@dataclass(frozen=True)
class RegisteredCompany:
    id: str
    name: str
    aliases: tuple[str, ...]
    industry: str
    priority: int
    official_domains: tuple[str, ...]
    sources: tuple[RegisteredSource, ...]


@dataclass(frozen=True)
class CompanySourceRegistry:
    schema_version: int
    updated_at: str
    collection_scope: tuple[str, ...]
    companies: tuple[RegisteredCompany, ...]

    def get_company(self, company_id: str) -> RegisteredCompany | None:
        return next(
            (company for company in self.companies if company.id == company_id),
            None,
        )

    def get_source(self, source_id: str) -> RegisteredSource | None:
        for company in self.companies:
            source = next(
                (item for item in company.sources if item.id == source_id),
                None,
            )
            if source is not None:
                return source
        return None

    def enabled_sources(self) -> tuple[RegisteredSource, ...]:
        return tuple(
            source
            for company in self.companies
            for source in company.sources
            if source.enabled
        )


def load_company_source_registry(
    path: str | Path = DEFAULT_SOURCE_REGISTRY_PATH,
) -> CompanySourceRegistry:
    """Load and validate the official-source registry.

    Unlike the legacy crawler configuration, malformed registry data fails
    loudly.  Falling back to permissive defaults would make compliance state
    ambiguous and could accidentally enable an unreviewed source.
    """

    registry_path = Path(path)
    try:
        raw = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceRegistryError(
            f"Cannot load company source registry: {registry_path}"
        ) from exc

    return _build_registry(raw)


def _build_registry(raw: dict[str, Any]) -> CompanySourceRegistry:
    if raw.get("schema_version") != 1:
        raise SourceRegistryError("Unsupported company source registry version")

    collection_scope = tuple(raw.get("collection_scope", ()))
    missing_scope = _REQUIRED_SCOPE.difference(collection_scope)
    if missing_scope:
        raise SourceRegistryError(
            f"Registry collection scope is incomplete: {sorted(missing_scope)}"
        )

    raw_companies = raw.get("companies")
    if not isinstance(raw_companies, list) or not raw_companies:
        raise SourceRegistryError("Registry must contain at least one company")

    company_ids: set[str] = set()
    source_ids: set[str] = set()
    companies: list[RegisteredCompany] = []

    for raw_company in raw_companies:
        company_id = _required_text(raw_company, "id", "company")
        if company_id in company_ids:
            raise SourceRegistryError(f"Duplicate company id: {company_id}")
        company_ids.add(company_id)

        official_domains = tuple(raw_company.get("official_domains", ()))
        if not official_domains:
            raise SourceRegistryError(
                f"Company {company_id} has no official domains"
            )

        raw_sources = raw_company.get("sources")
        if not isinstance(raw_sources, list) or not raw_sources:
            raise SourceRegistryError(f"Company {company_id} has no sources")

        sources: list[RegisteredSource] = []
        for raw_source in raw_sources:
            source_id = _required_text(raw_source, "id", f"company {company_id}")
            if source_id in source_ids:
                raise SourceRegistryError(f"Duplicate source id: {source_id}")
            source_ids.add(source_id)

            status = _required_text(raw_source, "status", f"source {source_id}")
            if status not in _SOURCE_STATUSES:
                raise SourceRegistryError(
                    f"Source {source_id} has invalid status: {status}"
                )

            automation_decision = _required_text(
                raw_source,
                "automation_decision",
                f"source {source_id}",
            )
            if automation_decision not in _AUTOMATION_DECISIONS:
                raise SourceRegistryError(
                    f"Source {source_id} has invalid automation decision"
                )

            collection_mode = _required_text(
                raw_source,
                "collection_mode",
                f"source {source_id}",
            )
            if collection_mode != "complete":
                raise SourceRegistryError(
                    f"Source {source_id} must use complete collection"
                )

            adapter_options = raw_source.get("adapter_options", {})
            if not isinstance(adapter_options, dict):
                raise SourceRegistryError(
                    f"Source {source_id} adapter_options must be an object"
                )
            forbidden_options = _FORBIDDEN_COMPLETE_OPTIONS.intersection(
                adapter_options
            )
            if forbidden_options:
                raise SourceRegistryError(
                    f"Source {source_id} contains collection restrictions: "
                    f"{sorted(forbidden_options)}"
                )

            canonical_url = _required_text(
                raw_source,
                "canonical_url",
                f"source {source_id}",
            )
            job_list_url = _required_text(
                raw_source,
                "job_list_url",
                f"source {source_id}",
            )
            _validate_official_url(
                canonical_url,
                official_domains,
                source_id,
            )
            _validate_official_url(job_list_url, official_domains, source_id)

            enabled = raw_source.get("enabled") is True
            if enabled and (
                automation_decision != "allowed" or status != "enabled"
            ):
                raise SourceRegistryError(
                    f"Source {source_id} is enabled without an allowed decision"
                )

            sources.append(
                RegisteredSource(
                    id=source_id,
                    company_id=company_id,
                    source_type=_required_text(
                        raw_source,
                        "source_type",
                        f"source {source_id}",
                    ),
                    canonical_url=canonical_url,
                    job_list_url=job_list_url,
                    adapter=_required_text(
                        raw_source,
                        "adapter",
                        f"source {source_id}",
                    ),
                    adapter_options=dict(adapter_options),
                    collection_mode=collection_mode,
                    enabled=enabled,
                    status=status,
                    automation_decision=automation_decision,
                    robots_status=_required_text(
                        raw_source,
                        "robots_status",
                        f"source {source_id}",
                    ),
                    terms_status=_required_text(
                        raw_source,
                        "terms_status",
                        f"source {source_id}",
                    ),
                    last_reviewed_at=_required_text(
                        raw_source,
                        "last_reviewed_at",
                        f"source {source_id}",
                    ),
                    evidence_urls=tuple(raw_source.get("evidence_urls", ())),
                    notes=str(raw_source.get("notes", "")).strip(),
                )
            )

        companies.append(
            RegisteredCompany(
                id=company_id,
                name=_required_text(raw_company, "name", f"company {company_id}"),
                aliases=tuple(raw_company.get("aliases", ())),
                industry=_required_text(
                    raw_company,
                    "industry",
                    f"company {company_id}",
                ),
                priority=int(raw_company.get("priority", 1)),
                official_domains=official_domains,
                sources=tuple(sources),
            )
        )

    return CompanySourceRegistry(
        schema_version=1,
        updated_at=_required_text(raw, "updated_at", "registry"),
        collection_scope=collection_scope,
        companies=tuple(companies),
    )


def _required_text(raw: dict[str, Any], key: str, context: str) -> str:
    value = str(raw.get(key, "")).strip()
    if not value:
        raise SourceRegistryError(f"Missing {key} in {context}")
    return value


def _validate_official_url(
    url: str,
    official_domains: tuple[str, ...],
    source_id: str,
) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise SourceRegistryError(f"Source {source_id} must use an HTTPS URL")

    hostname = parsed.hostname.lower()
    allowed = any(
        hostname == domain.lower() or hostname.endswith(f".{domain.lower()}")
        for domain in official_domains
    )
    if not allowed:
        raise SourceRegistryError(
            f"Source {source_id} URL is outside its official domains: {url}"
        )
