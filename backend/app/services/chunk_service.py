from sqlmodel import Session, select

from app.models.entities import KnowledgeChunk


class ChunkServiceError(ValueError):
    """表示知识点业务处理中出现的可预期错误。"""


class ChunkService:
    """根据解析后的 section 结果生成并查询知识点实体。"""

    def create_chunks(self, document_id: int, sections: list[dict]) -> list[KnowledgeChunk]:
        """把 section 列表转换成知识点对象列表。"""
        chunks: list[KnowledgeChunk] = []

        for section in sections:
            chunks.append(
                KnowledgeChunk(
                    document_id=document_id,
                    section_title=section["section_title"],
                    section_level=section["section_level"],
                    section_path=section.get("section_path") or section["section_title"],
                    content=section["content"],
                )
            )

        return chunks

    def list_chunks(self, session: Session) -> list[KnowledgeChunk]:
        """返回当前系统中的知识点列表。"""
        statement = select(KnowledgeChunk).order_by(KnowledgeChunk.created_at.desc())
        return session.exec(statement).all()

    def get_chunk(self, session: Session, chunk_id: int) -> KnowledgeChunk:
        """按 id 返回单个知识点，不存在时抛出业务异常。"""
        chunk = session.get(KnowledgeChunk, chunk_id)
        if chunk is None:
            raise ChunkServiceError("知识点不存在。")
        return chunk


chunk_service = ChunkService()