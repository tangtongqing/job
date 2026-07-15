"""部分唯一索引测试：同一岗位同时只能有一个非终态投递。

对照返工任务 §6.5。
"""

import pytest
from sqlalchemy.exc import IntegrityError

from src.db.models import Application, APP_APPLIED, APP_OFFER_ACCEPTED, APP_OFFER_PENDING


def test_one_active_application_per_job(session, job_id):
    """同一 job 同时存在两个非终态 Application 应失败。"""
    with session.begin_nested():
        session.add(Application(job_id=job_id, status=APP_APPLIED))

    with pytest.raises(IntegrityError):
        with session.begin_nested():
            session.add(Application(job_id=job_id, status=APP_APPLIED))


def test_terminal_allows_new_application(session, job_id):
    """终态后允许新建非终态投递（如春招再投）。"""
    # 先建一个终态投递
    with session.begin_nested():
        session.add(Application(job_id=job_id, status=APP_OFFER_ACCEPTED))

    # 再建一个非终态投递应该成功
    with session.begin_nested():
        session.add(Application(job_id=job_id, status=APP_APPLIED))

    assert session.query(Application).filter_by(job_id=job_id).count() == 2
