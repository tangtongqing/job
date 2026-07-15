"""采集适配器基类。

对应 crawler-module.md §2.1：
- HTTP client 懒加载（不在 __init__ 触网）
- 支持 should_crawl / fetch / parse / crawl
- 支持注入 fake client（测试不触网）
"""

from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from typing import Any, Callable, Protocol

logger = logging.getLogger(__name__)


class HttpClient(Protocol):
    """HTTP 客户端接口（便于注入 fake）。"""

    def get(self, url: str, **kwargs: Any) -> Any: ...


class BaseAdapter(ABC):
    """采集适配器基类。

    初始化不触网。HTTP client 懒加载，支持注入 fake。
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.source_name: str = self.config.get("source_name", "unknown")
        self._client: Any | None = None  # 懒加载

    @property
    def client(self) -> Any:
        """HTTP 客户端懒加载（仅用到时才创建）。"""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> Any:
        """创建 httpx.Client（子类可 override 用 Playwright 等）。"""
        import httpx

        return httpx.Client(
            timeout=self.config.get("timeout", 30),
            headers={"User-Agent": self._get_random_ua()},
        )

    @abstractmethod
    def should_crawl(self) -> bool:
        """合规检查：是否允许采集。"""
        ...

    @abstractmethod
    def fetch(self, page: int = 1) -> list[dict]:
        """抓取岗位列表，返回原始数据列表。"""
        ...

    @abstractmethod
    def parse(self, raw_data: dict) -> dict | None:
        """解析单条岗位数据，返回结构化 dict 或 None（解析失败）。"""
        ...

    def crawl(self) -> list[dict]:
        """完整采集流程：fetch + parse。返回解析后的岗位列表。"""
        if not self.should_crawl():
            logger.info(f"[{self.source_name}] should_crawl=False，跳过采集")
            return []

        raw_list = self.fetch()
        parsed: list[dict] = []
        for raw in raw_list:
            try:
                p = self.parse(raw)
                if p is not None:
                    parsed.append(p)
            except Exception as e:
                logger.warning(f"[{self.source_name}] 解析失败: {e}")
        return parsed

    def close(self) -> None:
        """释放资源。"""
        if self._client is not None:
            close = getattr(self._client, "close", None)
            if close:
                close()
            self._client = None

    def _get_random_ua(self) -> str:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        ]
        return random.choice(user_agents)
