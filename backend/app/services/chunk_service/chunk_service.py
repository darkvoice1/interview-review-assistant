from __future__ import annotations

from sqlmodel import Session

from app.models.entities import KnowledgeChunk

from .chunk_query_service import chunk_query_service


class ChunkServiceError(ValueError):
    """表示知识点业务处理中出现的可预期错误。"""


class ChunkService:
    """对外统一暴露知识点生成与查询能力。"""

    def create_chunks(self, document_id: int, sections: list[dict], session: Session | None = None) -> list[KnowledgeChunk]:
        """把 section 列表转换成更细粒度的知识点对象列表。"""
        from .chunk_generation_service import chunk_generation_service

        return chunk_generation_service.create_chunks(document_id, sections, session=session)

    def list_chunks(self, session: Session) -> list[KnowledgeChunk]:
        """返回当前系统中的知识点列表。"""
        return chunk_query_service.list_chunks(session)

    def get_chunk(self, session: Session, chunk_id: int) -> KnowledgeChunk:
        """按 id 返回单个知识点，不存在时抛出业务异常。"""
        try:
            return chunk_query_service.get_chunk(session, chunk_id)
        except ValueError as exc:
            raise ChunkServiceError(str(exc)) from exc


chunk_service = ChunkService()
