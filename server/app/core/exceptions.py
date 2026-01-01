from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "code": getattr(exc, 'code', 'HTTP_EXCEPTION')},
        )

    elif isinstance(exc, SQLAlchemyError):
        logger.error(f"数据库错误: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "数据库操作失败", "code": "DATABASE_ERROR"},
        )

    else:
        logger.error(f"未处理的异常: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误", "code": "INTERNAL_ERROR"},
        )


def create_http_exception(status_code: int, detail: str, code: str = None):
    """创建自定义HTTP异常"""
    exc = HTTPException(status_code=status_code, detail=detail)
    if code:
        exc.code = code
    return exc
