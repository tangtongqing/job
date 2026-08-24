"""本地与作品集演示环境控制。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.responses import ForbiddenError
from src.config import get_settings
from src.db.demo_data import seed_demo_data
from src.db.session import get_db

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/reset")
def reset_demo(db: Session = Depends(get_db)):
    """恢复确定性的完整演示场景；生产部署可通过环境变量关闭。"""
    if not get_settings().demo_reset_enabled:
        raise ForbiddenError("当前环境已关闭 Demo 数据重置")
    summary = seed_demo_data(db, replace=True)
    return {"data": {"message": "Demo 数据已重置", **summary}}
