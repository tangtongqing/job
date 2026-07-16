"""采集管理路由（api-contract.md 模块 G）。

POST /crawler/trigger  手动触发采集
GET  /crawler/logs     采集日志
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.models import CrawlLog
from src.crawler.service import CrawlService
from src.api.responses import make_paginated, ValidationError

router = APIRouter(prefix="/crawler", tags=["crawler"])


class TriggerRequest(BaseModel):
    source: str | None = None  # None → 按配置触发 enabled sources


# 支持注入 fake service（测试用）
_service_override: CrawlService | None = None


def set_service_for_testing(service: CrawlService | None) -> None:
    """测试注入：覆盖默认 service（避免触网）。"""
    global _service_override
    _service_override = service


def _get_service() -> CrawlService:
    return _service_override or CrawlService()


@router.post("/trigger")
def trigger(payload: TriggerRequest, db: Session = Depends(get_db)):
    """手动触发采集。可指定 source，或触发所有 enabled。"""
    service = _get_service()
    source = payload.source

    if source is None:
        results = []
        for enabled_source in service.config.enabled_source_names():
            log = service.crawl_source(db, enabled_source)
            results.append(_dump_log(log))
        return {"data": {"results": results, "total": len(results)}}

    log = service.crawl_source(db, source)
    return {"data": _dump_log(log)}


def _dump_log(log: CrawlLog) -> dict:
    return {
        "source": log.source,
        "status": log.status,
        "count": log.count,
        "error": log.error,
    }


@router.get("/logs")
def logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """采集日志列表（分页 + 按 source/status 筛选）。"""
    q = select(CrawlLog)
    if source:
        q = q.where(CrawlLog.source == source)
    if status:
        q = q.where(CrawlLog.status == status)

    total = db.scalar(select(func.count()).select_from(q.subquery()))
    q = q.order_by(CrawlLog.started_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = db.scalars(q).all()

    return make_paginated(
        [
            {
                "id": r.id,
                "source": r.source,
                "status": r.status,
                "count": r.count,
                "error": r.error,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            }
            for r in rows
        ],
        page,
        page_size,
        total,
    )


@router.get("/sources")
def sources(db: Session = Depends(get_db)):
    """Return configured source health without exposing internal credentials."""
    service = _get_service()
    result = []
    for name, cfg in service.config.sources.items():
        latest = db.scalar(
            select(CrawlLog)
            .where(CrawlLog.source == name)
            .order_by(CrawlLog.started_at.desc())
            .limit(1)
        )
        result.append(
            {
                "name": name,
                "label": cfg.options.get("company") or name,
                "adapter": cfg.adapter,
                "enabled": cfg.enabled,
                "kind": "public_api" if cfg.adapter == "greenhouse" else "website" if cfg.adapter == "company" else "restricted_platform",
                "last_run": {
                    "status": latest.status,
                    "count": latest.count,
                    "error": latest.error,
                    "finished_at": latest.finished_at.isoformat() if latest.finished_at else None,
                } if latest else None,
            }
        )
    return {"data": result}
