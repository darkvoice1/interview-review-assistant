from fastapi import APIRouter

from app.api.chunks import router as chunks_router
from app.api.documents import router as documents_router
from app.api.questions import router as questions_router
from app.api.review import router as review_router
from app.api.settings import router as settings_router
from app.api.system import router as system_router

api_router = APIRouter()
api_router.include_router(system_router, tags=["system"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(chunks_router, prefix="/chunks", tags=["chunks"])
api_router.include_router(questions_router, prefix="/questions", tags=["questions"])
api_router.include_router(review_router, prefix="/review", tags=["review"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])