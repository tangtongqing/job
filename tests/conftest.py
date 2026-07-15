"""pytest 配置：用内存 SQLite，不污染 data/jobpulse.db。"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.db.session import Base
import src.db.models  # noqa: F401  触发模型注册


@pytest.fixture()
def engine():
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def session(engine):
    conn = engine.connect()
    s = Session(bind=conn)
    yield s
    s.close()
    conn.close()


@pytest.fixture()
def job_id(session):
    """建一个合法 Job，返回 id（给需要外键的测试用）。"""
    from src.db.models import Job

    with session.begin_nested():
        session.add(Job(company="测试公司", title="测试岗位", source="boss"))
    return session.query(Job).first().id


@pytest.fixture()
def application_id(session, job_id):
    """建一个 applied 状态的投递，返回 id。"""
    from src.db.models import Application, APP_APPLIED

    with session.begin_nested():
        session.add(Application(job_id=job_id, status=APP_APPLIED))
    return session.query(Application).first().id
