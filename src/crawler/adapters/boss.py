"""BOSS 直聘适配器骨架（高风险，默认禁用，安全降级）。

对应 crawler-module.md §2.2 BossAdapter：
- 不做登录、验证码绕过、反爬规避
- 遇到验证码/登录页/403/robots禁止 → 安全跳过，记录失败
- 仅作为合规骨架存在，不实际抓取
"""

from __future__ import annotations

import logging

from src.crawler.adapters.base import BaseAdapter
from src.crawler.compliance.robots import RobotsChecker

logger = logging.getLogger(__name__)


class BossAdapter(BaseAdapter):
    """BOSS 直聘适配器（合规骨架，默认安全降级）。

    严格不做：登录、验证码绕过、反爬规避、代理池。
    遇到任何访问障碍 → 安全跳过，记录失败。
    """

    def __init__(self, config: dict | None = None, robots_checker: RobotsChecker | None = None):
        super().__init__(config)
        self.robots_checker = robots_checker or RobotsChecker()
        self.base_url = self.config.get("base_url", "https://www.zhipin.com")

    def should_crawl(self) -> bool:
        """BOSS 默认高风险，robots 必须显式允许才采集。"""
        # robots fail-closed：无法确认允许 → 禁止
        if not self.robots_checker.can_fetch(self.base_url):
            logger.info("[boss] robots 禁止或无法确认，安全跳过")
            return False
        return True

    def fetch(self, page: int = 1) -> list[dict]:
        """安全骨架：不实际抓取，返回空列表。

        BOSS 反爬极强，任何尝试都伴随风险。本骨架明确不抓取，
        除非未来有合规的官方 API 接入。
        """
        logger.warning("[boss] BOSS 适配器为合规骨架，不实际抓取")
        return []

    def parse(self, raw_data: dict) -> dict | None:
        """BOSS 不实际解析。"""
        return None
