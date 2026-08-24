"""数据库初始化脚本：安全迁移 + 填演示种子数据。

用法：
    python -m src.db.init_db

验证用，非生产数据。种子数据对应 web/dashboard-data.ts 的演示数据，
确保前后端演示数据一致。
"""

from src.config import get_settings
from src.db.demo_data import seed_demo_data
from src.db.schema_migrations import upgrade_database
from src.db.session import SessionLocal


def init_db():
    """将 schema 升级到 head，再写入幂等 Demo 种子。"""
    migration = upgrade_database(get_settings().database_url)
    print(f"[init_db] 数据库结构就绪：{migration.action} @ {migration.current_revision}")
    if migration.backup_path is not None:
        print(f"[init_db] 升级前备份：{migration.backup_path}")

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
