"""FastAPI 应用入口。

这个文件主要负责三件事：
1. 创建并配置 FastAPI 应用实例。
2. 注册全局中间件、异常处理和 API 路由。
3. 提供既能被 `uvicorn backend.main:app` 引用、又能被 VSCode 直接运行的启动入口。
"""

from __future__ import annotations

from contextlib import asynccontextmanager

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    # 兼容直接执行 `python backend/main.py` 的场景。
    # 这时解释器默认只知道当前文件所在目录，手动补一层项目根目录后，
    # `from backend...` 这样的导入才能正常工作。
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1 import api_router
from backend.app.core.config import settings
from backend.app.core.exceptions import AppError
from backend.app.core.response import error_response, success_response
from backend.app.services.rag_service import get_rag_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
# 模块级 logger 统一复用，方便后续从启动日志里排查预热或接口异常。
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时预热 RAG 检索链路。"""
    if settings.prewarm_rag_on_startup:
        try:
            summary = get_rag_service().prewarm_for_serving()
            logger.info("RAG prewarm summary: %s", summary)
        except Exception as exc:  # pragma: no cover - startup environment varies
            logger.warning("RAG prewarm failed: %s", exc)
    else:
        logger.info("RAG prewarm disabled by configuration.")
    yield


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。

    单独拆成工厂函数有两个好处：
    1. 测试时可以按需创建全新 app，而不是依赖导入副作用。
    2. 后续如果增加开发/测试/生产环境差异化初始化逻辑，扩展点会更清晰。
    """

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    # 当允许所有来源时，浏览器规范不允许同时带 allow_credentials=True，
    # 这里根据 origin 配置自动做一个兼容处理，避免前端本地联调时报 CORS 问题。
    allow_credentials = settings.allowed_origins != ["*"]

    # 目前前端和 Swagger 文档都会直接访问这个后端，因此 CORS 放在应用层统一处理。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        # 业务异常已经带有明确的状态码和 message，直接按统一包络返回即可。
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.message, code=exc.code),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        # FastAPI/Pydantic 的校验错误默认结构偏底层，这里转成项目统一响应格式，
        # 方便前端直接读取 `message` 与 `data` 做提示。
        errors = jsonable_encoder(exc.errors())
        return JSONResponse(
            status_code=422,
            content=error_response("请求参数校验失败", code=422, data=errors),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        # 兜底异常必须保留完整日志，方便定位线上问题；对外只暴露统一错误文案。
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content=error_response("服务器内部错误", code=500),
        )

    # 全部 Ver 2.0 API 都挂在统一前缀下，便于后续版本演进和网关转发。
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/", tags=["root"])
    async def root() -> dict:
        # 根路径只提供一个轻量入口说明，真正的接口说明以 `/docs` 为准。
        return success_response(
            {
                "message": settings.app_name,
                "docs": "/docs",
                "api_prefix": settings.api_prefix,
            }
        )

    return app


app = create_app()


def main() -> None:
    """供 VSCode 直接运行的本地启动入口。

    这里复用 `settings` 里的 host/port，保证它和命令行
    `uvicorn backend.main:app --host ... --port ...` 的行为保持一致。
    `reload=False` 是为了让断点调试更稳定，避免热重载派生子进程影响调试体验。
    """

    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
