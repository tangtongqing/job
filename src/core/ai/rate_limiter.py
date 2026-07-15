"""AI 限流器。

对应 ai-parser-module.md §4.4 成本控制：
每分钟最大调用数，超限直接降级正则。
"""

from __future__ import annotations

import time
from collections import deque


class AIRateLimiter:
    """滑动窗口限流（每分钟 N 次）。"""

    def __init__(self, max_per_minute: int = 10, clock=None):
        self._max = max_per_minute
        self._window: deque[float] = deque()
        self._clock = clock or time.monotonic

    def allow(self) -> bool:
        """检查是否允许调用。允许则记录，拒绝返回 False。"""
        now = self._clock()
        # 清理 60 秒外的记录
        while self._window and now - self._window[0] > 60:
            self._window.popleft()
        if len(self._window) >= self._max:
            return False
        self._window.append(now)
        return True

    def reset(self) -> None:
        self._window.clear()
