"""robots.txt 检查器（fail-closed 策略）。

对应 crawler-module.md §7.1：
- 无法读取 robots.txt 时默认禁止（fail-closed），不默认允许
- 支持人工显式 override
- 测试可注入 fake fetcher，不触网
"""

from __future__ import annotations

import logging
from typing import Callable, Protocol
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)


class RobotsFetcher(Protocol):
    """robots.txt 读取器接口（便于测试注入 fake）。"""

    def __call__(self, base_url: str) -> str | None:
        """返回 robots.txt 内容，失败返回 None。"""
        ...


def _default_fetcher(base_url: str) -> str | None:
    """默认实现：真实 HTTP 读取 robots.txt。失败返回 None。"""
    import httpx

    try:
        r = httpx.get(f"{base_url}/robots.txt", timeout=10, follow_redirects=True)
        if r.status_code == 200:
            return r.text
        return None
    except Exception as e:
        logger.debug(f"[ROBOTS] 读取 {base_url}/robots.txt 失败: {e}")
        return None


class RobotsChecker:
    """robots.txt 检查器。

    fail-closed 策略（crawler-module.md §7.1 v2 关键修正）：
    读取失败/超时/解析失败 → 默认禁止抓取，等待人工评估。
    """

    def __init__(
        self,
        fetcher: RobotsFetcher | None = None,
        manual_override: bool = False,
    ):
        self._fetcher = fetcher or _default_fetcher
        self._cache: dict[str, RobotFileParser] = {}
        self._unreadable: set[str] = set()
        self._manual_allowed: set[str] = set()
        self._manual_override_global = manual_override

    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        """检查是否允许抓取（fail-closed）。"""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # 人工显式允许（仅当全局开关开启时覆盖 fail-closed）
        if self._manual_override_global and base_url in self._manual_allowed:
            return True

        # 已标记为不可读 → fail-closed 禁止
        if base_url in self._unreadable:
            return False

        # 缓存命中
        if base_url in self._cache:
            return self._cache[base_url].can_fetch(user_agent, url)

        # 首次读取 robots.txt
        content = self._fetcher(base_url)
        if content is None:
            # fail-closed：无法确认允许 → 禁止
            logger.warning(
                f"[ROBOTS] 无法读取 {base_url}/robots.txt，"
                f"按 fail-closed 策略禁止抓取，需人工评估"
            )
            self._unreadable.add(base_url)
            return False

        try:
            rp = RobotFileParser()
            rp.parse(content.splitlines())
            self._cache[base_url] = rp
            return rp.can_fetch(user_agent, url)
        except Exception as e:
            logger.warning(f"[ROBOTS] 解析 {base_url}/robots.txt 失败: {e}，fail-closed")
            self._unreadable.add(base_url)
            return False

    def mark_allowed_manually(self, base_url: str) -> bool:
        """人工评估后手动标记允许（覆盖 fail-closed）。"""
        if not self._manual_override_global:
            logger.warning(f"[ROBOTS] manual override 未开启，忽略 {base_url}")
            return False
        self._unreadable.discard(base_url)
        self._manual_allowed.add(base_url)
        logger.info(f"[ROBOTS] {base_url} 已被人工标记为允许抓取")
        return True
