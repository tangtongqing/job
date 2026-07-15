"""AI 解析缓存。

对应 TASK-BE-AI-001 §6 隐私：
- cache key 用 hash，不用明文
- cache value 只存 ParsedEmailResult，不存 email_text
"""

from __future__ import annotations

import hashlib
import time
from collections import OrderedDict

from src.core.ai.schemas import ParsedEmailResult


def text_hash(text: str) -> str:
    """邮件文本 hash（SHA256 前 16 位）。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class TTLCache:
    """简易 TTL 缓存（LRU + 过期淘汰）。不依赖外部库。"""

    def __init__(self, ttl: int = 3600, max_size: int = 100):
        self._ttl = ttl
        self._max_size = max_size
        self._store: OrderedDict[str, tuple[float, ParsedEmailResult]] = OrderedDict()

    def get(self, key: str) -> ParsedEmailResult | None:
        """获取缓存。key 应为 hash，不是原文。"""
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.time() - ts > self._ttl:
            del self._store[key]
            return None
        # LRU：移到末尾
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: ParsedEmailResult) -> None:
        """写入缓存。"""
        self._store[key] = (time.time(), value)
        self._store.move_to_end(key)
        # 超 max_size 淘汰最老
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)
