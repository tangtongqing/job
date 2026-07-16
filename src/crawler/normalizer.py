"""字段规范化（crawler-module.md §4 清洗与字段提取）。

将采集的原始字段归一化，避免因字符串不一致漏去重。
"""

from __future__ import annotations

import re


# ---------- 地点 ----------

# 常见变体 → 标准写法
_LOCATION_ALIASES: dict[str, str] = {
    "北京市": "北京",
    "上海市": "上海",
    "广州市": "广州",
    "深圳市": "深圳",
    "杭州市": "杭州",
    "成都市": "成都",
    "南京市": "南京",
    "武汉市": "武汉",
    "西安市": "西安",
    "beijing": "北京",
    "shanghai": "上海",
    "guangzhou": "广州",
    "shenzhen": "深圳",
    "hangzhou": "杭州",
}


def normalize_location(raw: str | None) -> str | None:
    """归一化地点：去"市"、统一别名、去多余空格。"""
    if not raw:
        return None
    s = raw.strip()
    # 别名映射
    lower = s.lower()
    if lower in _LOCATION_ALIASES:
        return _LOCATION_ALIASES[lower]
    if s in _LOCATION_ALIASES:
        return _LOCATION_ALIASES[s]
    # 去"市"后缀
    if s.endswith("市") and len(s) > 2:
        s = s[:-1]
    return s


# ---------- 公司 ----------

_COMPANY_SUFFIXES = [
    "有限公司",
    "有限责任公司",
    "股份有限公司",
    "集团",
    "科技有限公司",
    "网络有限公司",
    "信息技术有限公司",
]


def normalize_company(raw: str | None) -> str | None:
    """归一化公司名：去常见后缀、去多余空格、去"（XX）"地区后缀。"""
    if not raw:
        return None
    s = raw.strip()
    # 去 (XX) 地区括号
    s = re.sub(r"[（(][^（()）]*[)）]", "", s)
    s = s.strip()
    # 去常见公司后缀（从长到短匹配）
    for suffix in sorted(_COMPANY_SUFFIXES, key=len, reverse=True):
        if s.endswith(suffix):
            s = s[: -len(suffix)].strip()
            break
    return s


# ---------- 毕业年份 ----------

_YEAR_RE = re.compile(r"(20\d{2})")


def extract_graduation_year(raw: str | None) -> str | None:
    """从文本提取毕业年份（如"2026届"→"2026"）。"""
    if not raw:
        return None
    m = _YEAR_RE.search(raw)
    return m.group(1) if m else None


# ---------- 学历 ----------

_EDU_MAP = {
    "大专": "大专",
    "本科": "本科",
    "硕士": "硕士",
    "博士": "博士",
    "bachelor": "本科",
    "master": "硕士",
    "phd": "博士",
    "college": "大专",
}


def extract_education(raw: str | None) -> str | None:
    """提取学历要求。"""
    if not raw:
        return None
    s = raw.lower()
    for kw, std in _EDU_MAP.items():
        if kw in s:
            return std
    return None


# ---------- 经验 ----------

_EXP_PATTERNS = [
    (re.compile(r"(\d+)\s*[-~]\s*(\d+)\s*年"), "range"),
    (re.compile(r"(\d+)\s*\+?\s*年"), "min"),
    (re.compile(r"(\d+)\s*[-–~]\s*(\d+)\s*years?", re.I), "range_en"),
    (re.compile(r"(\d+)\s*\+?\s*years?", re.I), "min_en"),
    (re.compile(r"应届|不限|实习"), "any"),
    (re.compile(r"entry[- ]level|new grad|internship", re.I), "any_en"),
]


def extract_experience(raw: str | None) -> str | None:
    """提取经验要求。"""
    if not raw:
        return None
    s = raw.strip()
    for pat, _ in _EXP_PATTERNS:
        m = pat.search(s)
        if m:
            return m.group(0).strip()
    return None


# ---------- 岗位分类 ----------

_CATEGORY_RULES: dict[str, list[str]] = {
    "product": ["产品", "PM"],
    "tech": ["开发", "工程师", "后端", "前端", "算法", "架构", "测试", "运维", "data", "数据"],
    "design": ["设计", "UI", "UX", "视觉"],
    "operation": ["运营", "策划", "编辑", "市场", "BD"],
    "hr": ["HR", "人力", "招聘"],
    "finance": ["财务", "会计", "审计"],
}


def classify_job(title: str | None, jd: str | None = None) -> str | None:
    """按岗位名/JD 分类。返回英文 code 或 None。"""
    text = f"{title or ''} {jd or ''}".lower()
    for category, keywords in _CATEGORY_RULES.items():
        for kw in keywords:
            if kw.lower() in text:
                return category
    return None


def normalize_job(raw: dict) -> dict:
    """对原始岗位 dict 做完整规范化。"""
    title = raw.get("title")
    return {
        **raw,
        "company": normalize_company(raw.get("company")),
        "title": title.strip() if title else None,
        "location": normalize_location(raw.get("location")),
        "graduation_year": extract_graduation_year(raw.get("graduation_year_raw") or raw.get("graduation_year")),
        "education": extract_education(raw.get("education_raw") or raw.get("education")),
        "experience": extract_experience(raw.get("experience_raw") or raw.get("experience")),
        "job_category": raw.get("job_category") or classify_job(title, raw.get("jd")),
    }
