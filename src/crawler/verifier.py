"""岗位有效性核验（crawler-module.md §六 + PRD F-A.6）。

支持注入 fetcher（测试不触网）。
- 无效 → is_valid=False, status=closed, last_verified_at=now
- 有效 → 更新 last_verified_at, 保持 is_valid=True
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable, Protocol

from sqlalchemy.orm import Session

from src.db.models import Job, JOB_STATUS_DISPLAYING, JOB_STATUS_CLOSED

logger = logging.getLogger(__name__)


class VerifierFetcher(Protocol):
    """核验用的 URL 检查器接口（便于注入 fake）。"""

    def __call__(self, url: str) -> bool:
        """返回 True 表示岗位有效（如 200 且非关闭页），False 表示无效。"""
        ...


def _default_fetcher(url: str) -> bool:
    """默认实现：真实 HTTP 检查。200 视为有效。"""
    import httpx

    try:
        r = httpx.head(url, timeout=10, follow_redirects=True)
        return r.status_code == 200
    except Exception as e:
        logger.debug(f"[VERIFY] {url} 检查失败: {e}")
        return False


def verify_job(
    db: Session,
    job_id: int,
    fetcher: VerifierFetcher | None = None,
) -> Job:
    """核验单个岗位的有效性。

    Args:
        db: 数据库 session
        job_id: 岗位 id
        fetcher: 注入 URL 检查器（测试不触网）

    Returns:
        更新后的 Job

    Raises:
        NotFoundError: 岗位不存在
    """
    from src.api.responses import NotFoundError

    fetcher = fetcher or _default_fetcher
    job = db.get(Job, job_id)
    if job is None:
        raise NotFoundError(f"Job {job_id} not found")

    now = datetime.utcnow()
    url = job.apply_url or job.source_url or ""

    if not url:
        # 没有可核验的 URL → 保持原状，只更新核验时间
        job.last_verified_at = now
        db.commit()
        return job

    is_valid = fetcher(url)
    job.last_verified_at = now
    if is_valid:
        job.is_valid = True
        if job.status == JOB_STATUS_CLOSED:
            job.status = JOB_STATUS_DISPLAYING
    else:
        job.is_valid = False
        job.status = JOB_STATUS_CLOSED

    db.commit()
    db.refresh(job)
    return job
