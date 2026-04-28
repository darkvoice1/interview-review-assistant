from app.models.entities import KnowledgeChunk


# 知识点切分服务，负责把解析结果转换成可落库的知识点对象。
class ChunkService:
    """根据解析后的 section 结果生成知识点实体。"""

    def create_chunks(self, document_id: int, sections: list[dict]) -> list[KnowledgeChunk]:
        """把 section 列表转换成知识点对象列表。"""
        chunks: list[KnowledgeChunk] = []

        for section in sections:
            chunks.append(
                KnowledgeChunk(
                    document_id=document_id,
                    section_title=section["section_title"],
                    section_level=section["section_level"],
                    content=section["content"],
                )
            )

        return chunks


chunk_service = ChunkService()