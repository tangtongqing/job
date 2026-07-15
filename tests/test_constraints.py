"""CHECK 约束测试：非法枚举写入必须失败。

对照返工任务 §6.4。
"""

import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from src.db.models import (
    Job,
    Application,
    ApplicationEvent,
    UserJobAction,
    CrawlLog,
)


@pytest.mark.parametrize("bad_status", ["INVALID", "已投递", "applied2", ""])
def test_job_status_check(session, bad_status):
    """Job.status 非法值应被 CHECK 拦截。"""
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(Job(company="c", title="t", source="boss", status=bad_status))


def test_application_status_check(session, job_id):
    """Application.status 非法值应被拦截。"""
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(Application(job_id=job_id, status="BAD_STATUS"))


def test_event_type_check(session, application_id):
    """ApplicationEvent.event_type 非法值应被拦截。"""
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(ApplicationEvent(application_id=application_id, event_type="BAD"))


def test_action_type_check(session, job_id):
    """UserJobAction.action_type 非法值应被拦截。"""
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(UserJobAction(job_id=job_id, action_type="BAD"))


def test_crawl_status_check(session):
    """CrawlLog.status 非法值应被拦截。"""
    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(CrawlLog(source="boss", status="BAD", started_at=datetime.datetime.utcnow()))
