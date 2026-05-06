from __future__ import annotations

from sqlmodel import Session, select

from app.models.entities import KnowledgeChunk


class ChunkQueryService:
    """负责知识点查询相关能力。"""

    def list_chunks(self, session: Session) -> list[KnowledgeChunk]:
        """返回当前系统中的知识点列表。"""
        statement = select(KnowledgeChunk).order_by(KnowledgeChunk.created_at.desc(), KnowledgeChunk.chunk_index.asc())
        return session.exec(statement).all()

    def get_chunk(self, session: Session, chunk_id: int) -> KnowledgeChunk:
        """按 id 返回单个知识点，不存在时抛出业务异常。"""
        chunk = session.get(KnowledgeChunk, chunk_id)
        if chunk is None:
            raise ValueError("知识点不存在。")
        return chunk


chunk_query_service = ChunkQueryService()
