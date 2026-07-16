"""采集服务（crawler-module.md §三 + 返工任务 §5）。

核心流程（8 步）：
1. 根据 source 创建 adapter
2. should_crawl()；不允许 → CrawlLog(skipped)
3. fetch + parse
4. 规范化
5. 去重/合并
6. 批量写入 Job（batch_size）
7. 成功 → CrawlLog(success, count)
8. 异常 → CrawlLog(failed, error)；无论成功失败都 close adapter
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Job, CrawlLog, CRAWL_SUCCESS, CRAWL_FAILED, CRAWL_SKIPPED
from src.api.responses import ValidationError
from src.crawler.adapters.base import BaseAdapter
from src.crawler.adapters.factory import create_adapter
from src.crawler.compliance.robots import RobotsChecker
from src.crawler.config import CrawlerConfig, load_crawler_config
from src.crawler.normalizer import normalize_job
from src.crawler import dedup

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 20


class CrawlService:
    """采集服务，协调 adapter + normalizer + dedup + 持久化 + 日志。"""

    def __init__(
        self,
        batch_size: int | None = None,
        robots_checker=None,
        config: CrawlerConfig | None = None,
    ):
        self.config = config or load_crawler_config()
        self.batch_size = batch_size or self.config.global_config.batch_size
        self.robots_checker = robots_checker or RobotsChecker(
            manual_override=self.config.global_config.manual_robots_override
        )

    def crawl_source(
        self,
        db: Session,
        source: str,
        adapter: BaseAdapter | None = None,
        adapter_kwargs: dict | None = None,
    ) -> CrawlLog:
        """采集单个 source。

        Args:
            db: 数据库 session
            source: source 名（company/boss/nowcoder）
            adapter: 注入适配器（测试用 fake，不触网）
            adapter_kwargs: 创建适配器的额外参数

        Returns:
            CrawlLog 记录（success/skipped/failed）
        """
        adapter_kwargs = adapter_kwargs or {}
        started_at = datetime.utcnow()
        source_cfg = self.config.resolve_source(source)

        if adapter is None:
            if source_cfg is None:
                raise ValidationError(
                    f"未知采集源: {source}",
                    details={"source": source},
                )
            if not source_cfg.enabled:
                raise ValidationError(
                    f"采集源已禁用: {source}",
                    details={"source": source, "enabled": False},
                )
            adapter_config = {
                "source_name": source_cfg.name,
                **source_cfg.options,
                **adapter_kwargs.pop("config", {}),
            }
            adapter = create_adapter(
                source_cfg.adapter,
                config=adapter_config,
                robots_checker=self.robots_checker,
                **adapter_kwargs,
            )

        try:
            # 2. 合规检查
            if not adapter.should_crawl():
                logger.info(f"[CRAWL] {source} should_crawl=False，跳过")
                log = self._write_log(db, source, CRAWL_SKIPPED, started_at)
                return log

            # 3. fetch + parse
            raw_jobs = adapter.crawl()

            # 4. 规范化
            normalized = [normalize_job(j) for j in raw_jobs]

            # 5+6. 去重 + 批量写入
            saved = self._save_jobs(db, source, normalized)

            # 7. 成功
            return self._write_log(db, source, CRAWL_SUCCESS, started_at, count=saved)

        except Exception as e:
            logger.exception(f"[CRAWL] {source} 采集失败")
            db.rollback()
            return self._write_log(db, source, CRAWL_FAILED, started_at, error=str(e))

        finally:
            # 8. 无论成功失败都 close adapter（无论是否本方法创建）
            adapter.close()

    def _save_jobs(self, db: Session, source: str, jobs: list[dict]) -> int:
        """去重 + 批量写入 Job。返回成功写入数。"""
        # 同源去重
        unique = dedup.dedup_same_source(jobs)

        # 查已有 jobs（跨源合并依据）
        existing = db.scalars(select(Job)).all()
        existing_dicts = [
            {"id": j.id, "company": j.company, "title": j.title, "location": j.location,
             "salary": j.salary, "requirement": j.requirement, "deadline": j.deadline,
             "source_url": j.source_url, "jd": j.jd, "apply_url": j.apply_url,
             "education": j.education, "experience": j.experience, "graduation_year": j.graduation_year}
            for j in existing
        ]

        saved = 0
        batch: list[Job] = []
        for job_data in unique:
            # 跨源精确匹配 → 合并补齐
            dup = dedup.find_cross_source_duplicate(existing_dicts, job_data)
            if dup:
                merged = dedup.merge_into_existing(dup, job_data)
                # 更新已有 Job（只补缺失字段）
                job_obj = db.get(Job, dup["id"])
                if job_obj:
                    for field in ["salary", "requirement", "deadline", "source_url", "jd", "apply_url", "education", "experience", "graduation_year"]:
                        if not getattr(job_obj, field) and merged.get(field):
                            setattr(job_obj, field, merged[field])
                continue

            # 新岗位
            batch.append(self._dict_to_job(source, job_data))
            saved += 1

            if len(batch) >= self.batch_size:
                db.add_all(batch)
                db.commit()
                batch = []

        if batch:
            db.add_all(batch)
            db.commit()

        return saved

    def _dict_to_job(self, source: str, data: dict) -> Job:
        """规范化 dict → Job ORM。"""
        return Job(
            company=data.get("company") or "未知公司",
            title=data.get("title") or "未知岗位",
            location=data.get("location"),
            salary=data.get("salary"),
            jd=data.get("jd"),
            requirement=data.get("requirement"),
            apply_url=data.get("apply_url"),
            source=source,
            source_url=data.get("source_url"),
            job_category=data.get("job_category"),
            graduation_year=data.get("graduation_year"),
            education=data.get("education"),
            experience=data.get("experience"),
            published_at=data.get("published_at"),
            deadline=data.get("deadline"),
            is_intern=bool(data.get("is_intern", False)),
            is_fresh=bool(data.get("is_fresh", False)),
            is_valid=True,
        )

    def _write_log(
        self,
        db: Session,
        source: str,
        status: str,
        started_at: datetime,
        count: int = 0,
        error: str | None = None,
    ) -> CrawlLog:
        """写入 CrawlLog。"""
        log = CrawlLog(
            source=source,
            status=status,
            count=count,
            error=error,
            started_at=started_at,
            finished_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
