"""正则降级解析器。

对应 TASK-BE-AI-001 §4：
- 公司关键词覆盖主流公司
- 状态关键词覆盖 5 类
- 状态优先级：rejected > offer_pending > interviewing > test > applied
- 正则成功 confidence=0.5, degraded=true
- 正则失败 parsed=false
"""

from __future__ import annotations

import re

from src.core.ai.schemas import ParsedEmailResult

# 公司关键词（按长度降序，优先匹配长名）
COMPANY_KEYWORDS = [
    "字节跳动", "字节", "抖音",
    "阿里巴巴", "阿里", "淘宝", "天猫", "蚂蚁",
    "腾讯", "微信", "QQ",
    "美团", "大众点评",
    "京东",
    "百度",
    "网易",
    "快手",
    "小红书",
    "拼多多",
]

# 状态关键词 + 优先级（index 越小优先级越高）
_STATUS_RULES = [
    ("rejected", ["很遗憾", "未能通过", "不合适", "拒绝", "未通过", "遗憾"]),
    ("offer_pending", ["offer", "录用", "薪资", "入职", "发放 offer", "录用通知"]),
    ("interviewing", ["面试", "一面", "二面", "终面", "视频面试", "线下面试", "面试邀请"]),
    ("test", ["笔试", "测评", "在线考试", "能力测试", "考试"]),
    ("applied", ["简历已收到", "投递成功", "申请已提交", "已收到您的简历"]),
]


def _match_company(text: str) -> str | None:
    """匹配公司关键词。返回匹配到的公司名（标准化）。"""
    for kw in sorted(COMPANY_KEYWORDS, key=len, reverse=True):
        if kw in text:
            # 归一到主品牌名
            return _normalize_company_keyword(kw)
    return None


def _normalize_company_keyword(kw: str) -> str:
    """把子品牌归一到主公司名。"""
    mapping = {
        "字节": "字节跳动", "抖音": "字节跳动",
        "阿里": "阿里巴巴", "淘宝": "阿里巴巴", "天猫": "阿里巴巴", "蚂蚁": "阿里巴巴",
        "微信": "腾讯", "QQ": "腾讯",
        "大众点评": "美团",
    }
    return mapping.get(kw, kw)


def _match_status(text: str) -> tuple[str | None, list[str]]:
    """匹配状态关键词。按优先级返回（状态, 命中关键词列表）。"""
    text_lower = text.lower()
    for status, keywords in _STATUS_RULES:
        hits = [kw for kw in keywords if kw.lower() in text_lower]
        if hits:
            return status, hits
    return None, []


class RegexParser:
    """正则降级解析器。"""

    def parse(self, text: str) -> ParsedEmailResult:
        """解析邮件文本，返回 ParsedEmailResult。"""
        if not text or not text.strip():
            return ParsedEmailResult(parsed=False, degraded=True)

        company = _match_company(text)
        status, hits = _match_status(text)

        if not company and not status:
            return ParsedEmailResult(parsed=False, degraded=True)

        reasoning_parts = []
        if company:
            reasoning_parts.append(f"公司匹配：{company}")
        if hits:
            reasoning_parts.append(f"关键词匹配：{'+'.join(hits)}")

        return ParsedEmailResult(
            parsed=True,
            company=company,
            title=None,  # 正则不提取岗位名
            suggested_status=status,
            confidence=0.5,
            degraded=True,
            reasoning="；".join(reasoning_parts) if reasoning_parts else None,
        )
