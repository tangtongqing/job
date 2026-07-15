"""牛客网适配器骨架（高风险，默认禁用，安全降级）。

对应 crawler-module.md §2.2 NowcoderAdapter：
- 与 BossAdapter 同策略，合规骨架
- 不做登录/验证码绕过/反爬规避
"""

from __future__ import annotations

import logging

from src.crawler.adapters.base import BaseAdapter
from src.crawler.compliance.robots import RobotsChecker

logger = logging.getLogger(__name__)


class NowcoderAdapter(BaseAdapter):
    """牛客网适配器（合规骨架，默认安全降级）。"""

    def __init__(self, config: dict | None = None, robots_checker: RobotsChecker | None = None):
        super().__init__(config)
        self.robots_checker = robots_checker or RobotsChecker()
        self.base_url = self.config.get("base_url", "https://www.nowcoder.com")

    def should_crawl(self) -> bool:
        if not self.robots_checker.can_fetch(self.base_url):
            logger.info("[nowcoder] robots 禁止或无法确认，安全跳过")
            return False
        return True

    def fetch(self, page: int = 1) -> list[dict]:
        logger.warning("[nowcoder] 适配器为合规骨架，不实际抓取")
        return []

    def parse(self, raw_data: dict) -> dict | None:
        return None
