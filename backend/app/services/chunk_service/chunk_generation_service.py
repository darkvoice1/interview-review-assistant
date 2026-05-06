from __future__ import annotations

from sqlmodel import Session

from app.models.entities import KnowledgeChunk

from .chunk_enrichment_service import chunk_enrichment_service
from .chunk_split_service import chunk_split_service


class ChunkGenerationService:
    """负责根据 section 生成知识点 chunk。"""

    def create_chunks(self, document_id: int, sections: list[dict], session: Session | None = None) -> list[KnowledgeChunk]:
        """把 section 列表转换成更细粒度的知识点对象列表。"""
        chunks: list[KnowledgeChunk] = []

        for section in sections:
            section_chunks = self.build_chunks_for_section(document_id, section, session=session)
            chunks.extend(section_chunks)

        return chunks

    def build_chunks_for_section(
        self,
        document_id: int,
        section: dict,
        session: Session | None = None,
    ) -> list[KnowledgeChunk]:
        """把单个 section 拆成多个更合理的 chunk。"""
        blocks = chunk_split_service.split_section_blocks(section["content"])
        if not blocks:
            return [
                KnowledgeChunk(
                    document_id=document_id,
                    section_title=section["section_title"],
                    section_level=section["section_level"],
                    section_path=section.get("section_path") or section["section_title"],
                    chunk_index=0,
                    chunk_type="empty",
                    content="",
                )
            ]

        merged_blocks = chunk_split_service.merge_blocks(blocks)
        ai_blocks = chunk_enrichment_service.try_ai_regroup_blocks(session, merged_blocks) if session is not None else None
        regrouped_blocks = ai_blocks or merged_blocks
        enhanced_blocks = (
            chunk_enrichment_service.try_ai_enrich_blocks(session, section, regrouped_blocks)
            if session is not None
            else None
        )
        final_blocks = enhanced_blocks or regrouped_blocks

        return [
            KnowledgeChunk(
                document_id=document_id,
                section_title=section["section_title"],
                section_level=section["section_level"],
                section_path=section.get("section_path") or section["section_title"],
                chunk_index=index,
                chunk_type=block.block_type,
                content=block.content,
                summary=block.summary,
                tags=chunk_enrichment_service.join_tags(block.tags),
            )
            for index, block in enumerate(final_blocks)
        ]


chunk_generation_service = ChunkGenerationService()
