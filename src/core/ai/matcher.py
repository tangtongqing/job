"""投递匹配器。

对应 TASK-BE-AI-001 §5：
- 只读 Application + Job，不写库
- 只匹配非终态投递
- 归一化精确匹配（复用 crawler.normalizer），禁止 contains 主匹配
- 唯一匹配返回 id；多匹配 + 岗位不明确 → None
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Application, Job, TERMINAL_STATUSES
from src.crawler.normalizer import normalize_company

logger = logging.getLogger(__name__)


class ApplicationMatcher:
    """投递匹配器（只读，不写库）。"""

    def match(
        self,
        db: Session,
        company: str | None,
        title: str | None = None,
    ) -> int | None:
        """匹配非终态投递。返回 application_id 或 None。

        Args:
            db: 数据库 session
            company: 解析出的公司名
            title: 解析出的岗位名（可选）

        Returns:
            匹配的 application_id；0 或多个不明确时返回 None
        """
        if not company:
            return None

        target_company = normalize_company(company)
        if not target_company:
            return None

        # 查所有非终态投递 + 关联岗位
        rows = db.execute(
            select(Application, Job)
            .join(Job, Application.job_id == Job.id)
            .where(~Application.status.in_(list(TERMINAL_STATUSES)))
        ).all()

        # 归一化精确匹配公司
        candidates: list[tuple[int, str]] = []  # (app_id, job_title)
        for app, job in rows:
            job_company_norm = normalize_company(job.company) or ""
            if job_company_norm == target_company:
                candidates.append((app.id, job.title or ""))

        if len(candidates) == 0:
            return None
        if len(candidates) == 1:
            return candidates[0][0]

        # 多匹配：检查岗位名是否明确
        if title:
            title_clean = title.strip()
            # 精确匹配岗位名
            exact = [(aid, t) for aid, t in candidates if t == title_clean]
            if len(exact) == 1:
                return exact[0][0]

        # 多匹配且不明确 → None（让用户选）
        logger.debug(
            f"[MATCH] 公司 {target_company} 有 {len(candidates)} 个投递，岗位不明确"
        )
        return None
