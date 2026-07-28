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
from datetime import datetime, timedelta

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
    "哔哩哔哩",
    "小米",
    "大疆",
    "MiniMax",
    "Figma",
    "Webflow",
    "Intercom",
    "Stripe",
]

# 降级模式只提取边界明确的常见岗位名称，避免把整句通知误识别成岗位。
JOB_TITLE_KEYWORDS = [
    "智能硬件产品实习生",
    "Senior Product Manager, Growth",
    "Senior Product Manager, AI",
    "Product Manager, Cash Platform",
    "Product Manager, Code",
    "内容产品经理",
    "增长产品经理",
    "商家产品经理",
    "创作者产品经理",
    "移动端产品经理",
    "AI 产品经理",
    "AI产品经理",
    "社交产品策划",
    "产品运营",
    "产品经理",
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
    text_lower = text.lower()
    for kw in sorted(COMPANY_KEYWORDS, key=len, reverse=True):
        if kw.lower() in text_lower:
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


def _match_title(text: str) -> str | None:
    """匹配边界明确的常见岗位名，并统一空格形式。"""
    text_lower = text.lower()
    for title in sorted(JOB_TITLE_KEYWORDS, key=len, reverse=True):
        if title.lower() in text_lower:
            return "AI 产品经理" if title == "AI产品经理" else title
    return None


_ABSOLUTE_DATETIME_PATTERN = re.compile(
    r"(?:(?P<year>\d{4})[年/\-.])?"
    r"(?P<month>\d{1,2})[月/\-.]"
    r"(?P<day>\d{1,2})日?"
    r"\s*(?P<period>上午|下午|晚上|中午)?\s*"
    r"(?P<hour>\d{1,2})(?:[:：点时](?P<minute>\d{1,2}))?(?:分)?"
)
_RELATIVE_DATETIME_PATTERN = re.compile(
    r"(?P<relative>今天|明天|后天)"
    r"\s*(?P<period>上午|下午|晚上|中午)?\s*"
    r"(?P<hour>\d{1,2})(?:[:：点时](?P<minute>\d{1,2}))?(?:分)?"
)


def _normalize_hour(period: str | None, hour: int) -> int:
    if period in {"下午", "晚上"} and hour < 12:
        return hour + 12
    if period == "中午" and hour < 11:
        return hour + 12
    if period == "上午" and hour == 12:
        return 0
    return hour


def _match_scheduled_time(text: str, now: datetime | None = None) -> datetime | None:
    """提取明确的面试/测评时间；缺少日期或钟点时不推测。"""
    now = now or datetime.now()

    absolute = _ABSOLUTE_DATETIME_PATTERN.search(text)
    if absolute:
        values = absolute.groupdict()
        year = int(values["year"]) if values["year"] else now.year
        hour = _normalize_hour(values["period"], int(values["hour"]))
        minute = int(values["minute"] or 0)
        try:
            result = datetime(
                year,
                int(values["month"]),
                int(values["day"]),
                hour,
                minute,
            )
        except ValueError:
            return None

        # 未写年份时，只在日期明显跨年后才顺延，避免把刚过去的通知擅自改到下一年。
        if not values["year"] and result < now - timedelta(days=30):
            try:
                result = result.replace(year=year + 1)
            except ValueError:
                return None
        return result

    relative = _RELATIVE_DATETIME_PATTERN.search(text)
    if relative:
        values = relative.groupdict()
        day_offset = {"今天": 0, "明天": 1, "后天": 2}[values["relative"]]
        hour = _normalize_hour(values["period"], int(values["hour"]))
        minute = int(values["minute"] or 0)
        try:
            target_date = (now + timedelta(days=day_offset)).date()
            return datetime.combine(target_date, datetime.min.time()).replace(
                hour=hour,
                minute=minute,
            )
        except ValueError:
            return None

    return None


class RegexParser:
    """正则降级解析器。"""

    def parse(self, text: str) -> ParsedEmailResult:
        """解析邮件文本，返回 ParsedEmailResult。"""
        if not text or not text.strip():
            return ParsedEmailResult(parsed=False, degraded=True)

        company = _match_company(text)
        title = _match_title(text)
        status, hits = _match_status(text)
        interview_time = (
            _match_scheduled_time(text)
            if status in {"interviewing", "test"}
            else None
        )

        if not company and not title and not status:
            return ParsedEmailResult(parsed=False, degraded=True)

        reasoning_parts = []
        if company:
            reasoning_parts.append(f"公司匹配：{company}")
        if title:
            reasoning_parts.append(f"岗位匹配：{title}")
        if hits:
            reasoning_parts.append(f"关键词匹配：{'+'.join(hits)}")
        if interview_time:
            reasoning_parts.append(
                f"计划时间：{interview_time.strftime('%Y-%m-%d %H:%M')}"
            )

        return ParsedEmailResult(
            parsed=True,
            company=company,
            title=title,
            suggested_status=status,
            interview_time=interview_time,
            confidence=0.5,
            degraded=True,
            reasoning="；".join(reasoning_parts) if reasoning_parts else None,
        )
