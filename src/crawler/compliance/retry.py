"""指数退避重试（crawler-module.md §7.2 v2 补充）。

测试可注入 sleeper/random，不真实长时间 sleep。
"""

from __future__ import annotations

import logging
import random as _random
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    func: Callable[..., T],
    *args: Any,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    sleeper: Callable[[float], None] | None = None,
    rng: Callable[[], float] | None = None,
    **kwargs: Any,
) -> T:
    """带指数退避的重试。

    Args:
        func: 要重试的函数
        max_retries: 最大重试次数（不含首次）
        base_delay: 基础延迟（秒），实际 = base_delay * 2^attempt + jitter
        max_delay: 单次最大延迟
        exceptions: 触发重试的异常类型
        sleeper: 注入 sleep 函数（测试用 fake）
        rng: 注入随机数生成（测试用固定值）

    Returns:
        func 的返回值

    Raises:
        最后一次异常（重试耗尽）
    """
    import time

    sleeper = sleeper or time.sleep
    rng = rng or _random.random

    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exc = e
            if attempt >= max_retries:
                logger.warning(
                    f"[RETRY] 重试 {attempt} 次后仍失败: {e}"
                )
                raise
            delay = min(base_delay * (2 ** attempt) + rng(), max_delay)
            logger.debug(f"[RETRY] 第 {attempt + 1} 次失败，{delay:.2f}s 后重试: {e}")
            sleeper(delay)

    # 不会到这里（循环要么 return 要么 raise），但 mypy 需要
    assert last_exc is not None
    raise last_exc
