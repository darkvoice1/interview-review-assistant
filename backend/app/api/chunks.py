from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.chunk import ChunkRead
from app.services.chunk_service import ChunkServiceError, chunk_service

# 知识点相关接口。
router = APIRouter()


@router.get("", response_model=list[ChunkRead])
def list_chunks(session: Session = Depends(get_session)) -> list[ChunkRead]:
    """返回当前系统中已经生成的知识点列表。"""
    chunks = chunk_service.list_chunks(session)
    return [ChunkRead.model_validate(chunk) for chunk in chunks]


@router.get("/{chunk_id}", response_model=ChunkRead)
def get_chunk(chunk_id: int, session: Session = Depends(get_session)) -> ChunkRead:
    """按 id 返回单个知识点详情。"""
    try:
        chunk = chunk_service.get_chunk(session, chunk_id)
    except ChunkServiceError as exc:
        # 服务层只抛业务异常，接口层负责转换成 HTTP 错误。
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ChunkRead.model_validate(chunk)
