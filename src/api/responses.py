"""统一响应封装 + 异常处理。

对应 api-contract.md §2.2/§2.4。
"""
from typing import Any, Generic, TypeVar

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0


class SuccessResponse(BaseModel, Generic[T]):
    data: T
    meta: Meta | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ---------- 业务异常 → HTTP 错误码映射（api-contract §2.4）----------


class APIError(Exception):
    """业务异常基类。子类定义 status_code 和 code。"""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class ValidationError(APIError):
    status_code = 400
    code = "VALIDATION_ERROR"


class InvalidTransitionError(APIError):
    status_code = 400
    code = "INVALID_TRANSITION"


class NotFoundError(APIError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(APIError):
    status_code = 409
    code = "CONFLICT"


# ---------- 异常处理器（注册到 app）----------


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
        ).model_dump(),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """FastAPI 参数/body 校验错误 → 统一 {error} envelope。

    对应 api-contract.md §2.4：VALIDATION_ERROR + HTTP 400。
    """
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="请求参数校验失败",
                details={"errors": exc.errors()},
            )
        ).model_dump(),
    )


def make_success(data: Any, meta: Meta | None = None) -> dict:
    """构造统一成功响应 dict。"""
    resp: dict[str, Any] = {"data": data}
    if meta is not None:
        resp["meta"] = meta.model_dump()
    return resp


def make_paginated(items: list[Any], page: int, page_size: int, total: int) -> dict:
    """构造分页成功响应。"""
    return make_success(items, Meta(page=page, page_size=page_size, total=total))
