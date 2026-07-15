"""调度器基础结构（crawler-module.md §三）。

不要求测试中真实启动后台循环。支持按配置注册 source 的 interval job。
挂载 FastAPI lifespan 时保证测试环境不产生不可控后台任务。
"""

from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)


class CrawlScheduler:
    """采集调度器（轻量封装，可接 APScheduler）。

    设计：不默认启动真实后台循环。注册的 job 列表可查，
    实际触发由外部（如 cron / 手动 API）或 lifespan 启动。
    """

    def __init__(self):
        self._jobs: list[dict] = []  # 注册的 job 描述
        self._scheduler = None  # APScheduler 实例（懒加载）

    def register_source(
        self,
        source: str,
        interval_minutes: int,
        callback: Callable | None = None,
    ) -> None:
        """注册一个 source 的定时任务。"""
        self._jobs.append({
            "source": source,
            "interval_minutes": interval_minutes,
            "callback": callback,
        })
        logger.info(f"[SCHED] 注册 {source} 每 {interval_minutes} 分钟采集")

    @property
    def jobs(self) -> list[dict]:
        return list(self._jobs)

    def start(self) -> None:
        """启动 APScheduler（仅生产/Demo 用，测试不调用）。

        若 APScheduler 未安装，记录 warning 并跳过。
        """
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger
        except ImportError:
            logger.warning("[SCHED] APScheduler 未安装，跳过后台调度")
            return

        if self._scheduler is not None:
            return

        self._scheduler = BackgroundScheduler()
        for job in self._jobs:
            if job["callback"] is None:
                continue
            self._scheduler.add_job(
                job["callback"],
                IntervalTrigger(minutes=job["interval_minutes"]),
                id=f"crawl_{job['source']}",
                replace_existing=True,
            )
        self._scheduler.start()
        logger.info("[SCHED] 后台调度已启动")

    def shutdown(self) -> None:
        """关闭调度器。"""
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("[SCHED] 后台调度已关闭")


# 全局单例（FastAPI lifespan 挂载用）
scheduler = CrawlScheduler()
