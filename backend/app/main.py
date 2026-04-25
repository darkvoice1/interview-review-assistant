from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import DOCUMENTS_DIR
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    # 应用启动时初始化数据库表。
    init_db()
    # 启动时提前创建上传目录，避免首次上传时报路径不存在。
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    yield


# 创建 FastAPI 应用实例。
app = FastAPI(
    title="Interview Review Assistant API",
    version="0.1.0",
    description="MVP backend for markdown-based interview review workflows.",
    lifespan=lifespan,
)

# 统一挂载 API 路由前缀。
app.include_router(api_router, prefix="/api")


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    # 返回服务基础信息，方便快速确认服务状态。
    return {
        "name": "interview-review-assistant",
        "status": "ok",
        "docs": "/docs",
    }