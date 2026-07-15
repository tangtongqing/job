"""JobPulse 后端入口（api-contract.md §2.1）。

Base URL: http://localhost:8000/api/v1
启动: uvicorn src.main:app --reload
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from src.api.responses import APIError, api_error_handler, validation_error_handler
from src.api.routes.app import (
    jobs,
    applications,
    dashboard,
    todo,
    crawler,
    user_actions,
    subscriptions,
    demo,
)

app = FastAPI(
    title="JobPulse API",
    description="大学生招聘信息聚合与投递管理 - 后端",
    version="0.1.0",
)

# CORS（前端 web/ 跑在 3000 端口）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3100",
        "http://127.0.0.1:3100",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册业务异常处理器
app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)


# v3 演进预留：鉴权中间件占位（M0 no-op）
@app.middleware("http")
async def auth_placeholder(request, call_next):
    """M0: no-op。M1 接 OAuth 后在此解析 token 注入 request.state.user。"""
    return await call_next(request)


# ---------- 路由注册（统一 /api/v1 前缀）----------
api_v1_prefix = "/api/v1"

app.include_router(jobs.router, prefix=api_v1_prefix)
app.include_router(applications.router, prefix=api_v1_prefix)
app.include_router(dashboard.router, prefix=api_v1_prefix)
app.include_router(todo.router, prefix=api_v1_prefix)
app.include_router(crawler.router, prefix=api_v1_prefix)
app.include_router(user_actions.router, prefix=api_v1_prefix)
app.include_router(subscriptions.router, prefix=api_v1_prefix)
app.include_router(demo.router, prefix=api_v1_prefix)


@app.get("/")
def root():
    return {"message": "JobPulse API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
