from fastapi import APIRouter

from app.api.chunks import router as chunks_router
from app.api.documents import router as documents_router
from app.api.review import router as review_router
from app.api.system import router as system_router

# 统一汇总所有业务路由。
api_router = APIRouter()
api_router.include_router(system_router, tags=["system"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(chunks_router, prefix="/chunks", tags=["chunks"])
api_router.include_router(review_router, prefix="/review", tags=["review"])