"""企业官网适配器（合规风险低）。

对应 crawler-module.md §2.2 CompanyWebsiteAdapter。
- 支持注入 fake fetcher / fake client，测试不触网
- 能解析本地 HTML / fixture，产出规范化岗位数据
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from src.crawler.adapters.base import BaseAdapter
from src.crawler.compliance.robots import RobotsChecker

logger = logging.getLogger(__name__)


class CompanyWebsiteAdapter(BaseAdapter):
    """企业官网采集适配器。

    支持注入 `html_fetcher`（接收 url 返回 HTML 文本），便于测试用 fixture。
    """

    def __init__(
        self,
        config: dict | None = None,
        robots_checker: RobotsChecker | None = None,
        html_fetcher: Callable[[str], str | None] | None = None,
    ):
        super().__init__(config)
        self.robots_checker = robots_checker or RobotsChecker()
        self.base_urls: list[str] = self.config.get("base_urls", [])
        self._html_fetcher = html_fetcher  # None 时用真实 HTTP

    def should_crawl(self) -> bool:
        """检查所有 base_url 的 robots。任意一个被禁则返回 False。"""
        for url in self.base_urls:
            if not self.robots_checker.can_fetch(url):
                logger.info(f"[company] robots 禁止抓取 {url}")
                return False
        return True

    def fetch(self, page: int = 1) -> list[dict]:
        """抓取所有 base_url 的 HTML，返回原始 HTML 字典列表。"""
        raw_list: list[dict] = []
        for url in self.base_urls:
            html = self._fetch_html(url)
            if html:
                raw_list.append({"url": url, "html": html})
        return raw_list

    def _fetch_html(self, url: str) -> str | None:
        """读取 URL 的 HTML（注入 fetcher 或真实 HTTP）。"""
        if self._html_fetcher is not None:
            return self._html_fetcher(url)
        try:
            r = self.client.get(url)
            r.raise_for_status()
            return r.text
        except Exception as e:
            logger.warning(f"[company] 抓取 {url} 失败: {e}")
            return None

    def parse(self, raw_data: dict) -> dict | None:
        """解析 HTML 提取岗位信息。

        默认实现用简单的 BeautifulSoup 提取。
        子类可 override 处理特定网站结构。
        """
        html = raw_data.get("html", "")
        url = raw_data.get("url", "")
        if not html:
            return None

        # 简单提取（真实场景需按网站结构定制）
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "lxml")
            title_tag = soup.find("title")
            title = title_tag.text.strip() if title_tag else ""

            # 尝试提取 job posting 元素（通用度低，仅占位）
            return {
                "company": self.config.get("company", ""),
                "title": title,
                "source_url": url,
                "raw_html": html[:500],  # 截断存原始片段
            }
        except Exception as e:
            logger.warning(f"[company] 解析失败: {e}")
            return None
