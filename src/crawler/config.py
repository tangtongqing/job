"""Crawler source configuration.

The project keeps crawler settings in ``config/sources.yaml``.  To avoid adding
another runtime dependency for this small M0 config shape, this module parses
the limited YAML subset used by that file and falls back to safe defaults.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config/sources.yaml")


@dataclass(frozen=True)
class CrawlerGlobalConfig:
    crawl_interval_minutes: int = 60
    max_concurrent: int = 2
    batch_size: int = 20
    manual_robots_override: bool = False


@dataclass(frozen=True)
class CrawlerSourceConfig:
    name: str
    adapter: str
    enabled: bool = False
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CrawlerConfig:
    global_config: CrawlerGlobalConfig
    sources: dict[str, CrawlerSourceConfig]

    def resolve_source(self, source: str) -> CrawlerSourceConfig | None:
        """Resolve by configured source key or adapter alias."""
        if source in self.sources:
            return self.sources[source]
        for cfg in self.sources.values():
            if cfg.adapter == source:
                return cfg
        return None

    def enabled_source_names(self) -> list[str]:
        """Return enabled configured source keys in stable order.

        Multiple companies may use the same adapter. Returning configuration
        keys keeps their logs, limits and company metadata independent.
        """
        return [name for name, cfg in self.sources.items() if cfg.enabled]


def _default_raw_config() -> dict[str, Any]:
    return {
        "global": {
            "crawl_interval_minutes": 60,
            "max_concurrent": 2,
            "batch_size": 20,
            "manual_robots_override": False,
        },
        "sources": {
            "company_website": {
                "enabled": False,
                "adapter": "company",
                "base_urls": [],
            },
            "boss": {"enabled": False, "adapter": "boss"},
            "nowcoder": {"enabled": False, "adapter": "nowcoder"},
        },
    }


def _strip_comment(line: str) -> str:
    return line.split("#", 1)[0].rstrip()


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(value)
                return parsed if isinstance(parsed, list) else value
            except (ValueError, SyntaxError):
                return value
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def _parse_sources_yaml(path: Path) -> dict[str, Any]:
    """Parse the simple mapping structure used by config/sources.yaml."""
    data: dict[str, Any] = {"global": {}, "sources": {}}
    section: str | None = None
    current_source: str | None = None
    current_list_key: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = _strip_comment(raw_line)
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        text = line.strip()

        if indent == 0 and text.endswith(":"):
            section = text[:-1]
            current_source = None
            current_list_key = None
            continue

        if section == "global" and indent >= 2 and ":" in text:
            key, value = text.split(":", 1)
            data["global"][key.strip()] = _parse_scalar(value)
            continue

        if section == "sources":
            if indent == 2 and text.endswith(":"):
                current_source = text[:-1]
                data["sources"].setdefault(current_source, {})
                current_list_key = None
                continue
            if (
                current_source
                and current_list_key
                and indent >= 6
                and text.startswith("-")
            ):
                data["sources"][current_source][current_list_key].append(
                    _parse_scalar(text[1:].strip())
                )
                continue
            if current_source and indent >= 4 and ":" in text:
                key, value = text.split(":", 1)
                key = key.strip()
                if not value.strip():
                    data["sources"][current_source][key] = []
                    current_list_key = key
                else:
                    data["sources"][current_source][key] = _parse_scalar(value)
                    current_list_key = None

    return data


def _build_config(raw: dict[str, Any]) -> CrawlerConfig:
    defaults = _default_raw_config()

    global_raw = {**defaults["global"], **raw.get("global", {})}
    global_config = CrawlerGlobalConfig(
        crawl_interval_minutes=int(global_raw.get("crawl_interval_minutes", 60)),
        max_concurrent=int(global_raw.get("max_concurrent", 2)),
        batch_size=int(global_raw.get("batch_size", 20)),
        manual_robots_override=bool(global_raw.get("manual_robots_override", False)),
    )

    source_raw = {**defaults["sources"], **raw.get("sources", {})}
    sources: dict[str, CrawlerSourceConfig] = {}
    for name, cfg in source_raw.items():
        adapter = str(cfg.get("adapter", name))
        options = {
            key: value
            for key, value in cfg.items()
            if key not in {"enabled", "adapter"}
        }
        sources[name] = CrawlerSourceConfig(
            name=name,
            adapter=adapter,
            enabled=bool(cfg.get("enabled", False)),
            options=options,
        )

    return CrawlerConfig(global_config=global_config, sources=sources)


@lru_cache
def load_crawler_config(path: str | Path = DEFAULT_CONFIG_PATH) -> CrawlerConfig:
    config_path = Path(path)
    if not config_path.exists():
        return _build_config(_default_raw_config())

    try:
        raw = _parse_sources_yaml(config_path)
    except Exception:
        raw = _default_raw_config()
    return _build_config(raw)
