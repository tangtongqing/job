"""速率限制器（按 source 独立）。

对应 crawler-module.md §7.2。
测试可注入 fake clock/sleeper，不真实 sleep。
"""

from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)


class RateLimiter:
    """每个 source 独立限频，避免全局互相影响。"""

    def __init__(
        self,
        min_interval: float = 60.0,
        sleeper: Callable[[float], None] | None = None,
        clock: Callable[[], float] | None = None,
    ):
        """
        Args:
            min_interval: 同一 source 两次请求最小间隔（秒），默认 60s
            sleeper: 注入 sleep 函数（测试用 fake，不真实阻塞）
            clock: 注入时间函数（测试用 fake）
        """
        import time

        self._min_interval = min_interval
        self._last_request: dict[str, float] = {}
        self._sleeper = sleeper or time.sleep
        self._clock = clock or time.monotonic

    def wait_if_needed(self, source: str) -> float:
        """如果距上次请求不足 min_interval，sleep 等待。返回实际等待秒数。"""
        now = self._clock()
        last = self._last_request.get(source, 0.0)
        elapsed = now - last
        wait = self._min_interval - elapsed
        if wait > 0:
            logger.debug(f"[RATE] {source} 限频等待 {wait:.2f}s")
            self._sleeper(wait)
        self._last_request[source] = self._clock()
        return max(0.0, wait)

    def reset(self, source: str | None = None) -> None:
        """重置 source 计时（或全部）。"""
        if source is None:
            self._last_request.clear()
        else:
            self._last_request.pop(source, None)
