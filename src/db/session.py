"""数据库 session 管理。

对应架构文档 system-architecture.md §7.4：
- get_engine() 支持 SQLite/PostgreSQL 切换（演进预留）
- SQLite 用 check_same_thread=False（FastAPI 线程池需要）
- 启用 PRAGMA foreign_keys = ON（SQLite 默认关外键约束）
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from src.config import get_settings

Base = declarative_base()

_settings = get_settings()

_engine_kwargs = {}
if _settings.is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(_settings.database_url, **_engine_kwargs)

# SQLite 启用外键约束
if _settings.is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI 依赖注入：每个请求一个 session。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
