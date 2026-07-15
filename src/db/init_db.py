"""数据库初始化脚本：建表 + 填演示种子数据。

用法：
    python -m src.db.init_db

验证用，非生产数据。种子数据对应 web/dashboard-data.ts 的演示数据，
确保前后端演示数据一致。
"""

from src.db.session import engine, SessionLocal, Base
from src.db.demo_data import seed_demo_data


def init_db():
    """建表 + 种子数据。"""
    # 建表
    Base.metadata.create_all(engine)
    print("[init_db] 表已创建")

    db = SessionLocal()
    try:
        summary = seed_demo_data(db)
        print(
            "[init_db] Demo 数据就绪："
            f"{summary['jobs']} 岗位 / {summary['applications']} 投递 / "
            f"{summary['saved_jobs']} 收藏与待投递 / {summary['subscriptions']} 订阅"
        )

    finally:
        db.close()


if __name__ == "__main__":
    init_db()
