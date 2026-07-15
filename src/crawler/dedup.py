"""去重/合并（crawler-module.md §五 + 返工要求）。

严格规则：
- 同源去重：(source, company, title, location) 规范化后精确匹配
- 跨源合并：只在 normalized (company, title, location) 精确相等时合并
- 禁止 contains/substring 作为合并依据
- 合并只补缺失字段，不覆盖已有更可靠字段
"""

from __future__ import annotations

from src.crawler.normalizer import normalize_company, normalize_location


def _norm_key(company: str | None, title: str | None, location: str | None) -> tuple[str, str, str]:
    """生成规范化后的去重键。None → 空串。"""
    c = normalize_company(company) or ""
    t = (title or "").strip()
    l = normalize_location(location) or ""
    return (c, t, l)


def find_same_source_duplicate(
    items: list[dict],
    new_item: dict,
) -> dict | None:
    """同源去重：在已入库/已处理列表里找精确匹配。

    匹配键：(normalized company, title, normalized location)
    返回匹配项或 None。
    """
    new_key = _norm_key(new_item.get("company"), new_item.get("title"), new_item.get("location"))
    for item in items:
        item_key = _norm_key(item.get("company"), item.get("title"), item.get("location"))
        if item_key == new_key:
            return item
    return None


def find_cross_source_duplicate(
    existing_jobs: list[dict],
    new_item: dict,
) -> dict | None:
    """跨源合并：在已有 Job 列表里找规范化精确匹配。

    严格只匹配 (company, title, location) 三字段精确相等（规范化后）。
    禁止 substring/contains 匹配。
    """
    new_key = _norm_key(new_item.get("company"), new_item.get("title"), new_item.get("location"))
    for job in existing_jobs:
        job_key = _norm_key(job.get("company"), job.get("title"), job.get("location"))
        if job_key == new_key:
            return job
    return None


def merge_into_existing(existing: dict, new_data: dict) -> dict:
    """合并：只补齐缺失字段，不覆盖已有更可靠字段。

    被补齐的字段：salary/requirement/deadline/source_url/jd 等。
    """
    merged = dict(existing)
    for field in ["salary", "requirement", "deadline", "source_url", "jd", "apply_url", "education", "experience", "graduation_year"]:
        # existing 为空且 new 有值 → 补齐
        if not merged.get(field) and new_data.get(field):
            merged[field] = new_data[field]
    return merged


def dedup_same_source(items: list[dict]) -> list[dict]:
    """对同一批采集结果做同源去重，返回去重后的列表。"""
    seen_keys: set[tuple] = set()
    result: list[dict] = []
    for item in items:
        key = _norm_key(item.get("company"), item.get("title"), item.get("location"))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        result.append(item)
    return result
