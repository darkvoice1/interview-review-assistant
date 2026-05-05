from __future__ import annotations

import json
import re
from dataclasses import dataclass

from sqlmodel import Session, select

from app.models.entities import KnowledgeChunk
from app.services.llm_service import llm_gateway_service


class ChunkServiceError(ValueError):
    """表示知识点业务处理中出现的可预期错误。"""


@dataclass
class SectionBlock:
    """描述 section 内部拆出的中间块结构。"""

    block_type: str
    content: str


class ChunkService:
    """根据解析后的 section 结果生成并查询知识点实体。"""

    ordered_list_pattern = re.compile(r"^\s*\d+[.)]\s+")
    unordered_list_pattern = re.compile(r"^\s*[-*+]\s+")
    image_pattern = re.compile(r"!\[[^\]]*\]\([^\)]+\)")

    def create_chunks(self, document_id: int, sections: list[dict], session: Session | None = None) -> list[KnowledgeChunk]:
        """把 section 列表转换成更细粒度的知识点对象列表。"""
        chunks: list[KnowledgeChunk] = []

        for section in sections:
            section_chunks = self._build_chunks_for_section(document_id, section, session=session)
            chunks.extend(section_chunks)

        return chunks

    def _build_chunks_for_section(
        self,
        document_id: int,
        section: dict,
        session: Session | None = None,
    ) -> list[KnowledgeChunk]:
        """把单个 section 拆成多个更合理的 chunk。"""
        blocks = self._split_section_blocks(section["content"])
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

        merged_blocks = self._merge_blocks(blocks)
        ai_blocks = self._try_ai_regroup_blocks(session, merged_blocks) if session is not None else None
        final_blocks = ai_blocks or merged_blocks

        return [
            KnowledgeChunk(
                document_id=document_id,
                section_title=section["section_title"],
                section_level=section["section_level"],
                section_path=section.get("section_path") or section["section_title"],
                chunk_index=index,
                chunk_type=block.block_type,
                content=block.content,
            )
            for index, block in enumerate(final_blocks)
        ]

    def _split_section_blocks(self, content: str) -> list[SectionBlock]:
        """按纯规则把 section 正文拆成段落块、列表块、代码块和图片块。"""
        if not content.strip():
            return []

        lines = content.splitlines()
        blocks: list[SectionBlock] = []
        buffer: list[str] = []
        in_code_block = False
        code_buffer: list[str] = []
        list_buffer: list[str] = []
        list_type: str | None = None

        def flush_paragraph() -> None:
            nonlocal buffer
            paragraph = "\n".join(buffer).strip()
            if paragraph:
                blocks.append(SectionBlock(block_type="paragraph", content=paragraph))
            buffer = []

        def flush_list() -> None:
            nonlocal list_buffer, list_type
            content_text = "\n".join(list_buffer).strip()
            if content_text:
                blocks.append(SectionBlock(block_type=list_type or "list", content=content_text))
            list_buffer = []
            list_type = None

        def flush_code() -> None:
            nonlocal code_buffer
            content_text = "\n".join(code_buffer).strip()
            if content_text:
                blocks.append(SectionBlock(block_type="code", content=content_text))
            code_buffer = []

        for raw_line in lines:
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            if stripped.startswith("```"):
                flush_paragraph()
                flush_list()
                if in_code_block:
                    code_buffer.append(line)
                    flush_code()
                    in_code_block = False
                else:
                    in_code_block = True
                    code_buffer = [line]
                continue

            if in_code_block:
                code_buffer.append(line)
                continue

            if self.image_pattern.fullmatch(stripped):
                flush_paragraph()
                flush_list()
                blocks.append(SectionBlock(block_type="image", content=stripped))
                continue

            current_list_type = self._detect_list_type(line)
            if current_list_type is not None:
                flush_paragraph()
                if list_type is not None and list_type != current_list_type:
                    flush_list()
                list_type = current_list_type
                list_buffer.append(line)
                continue

            if list_buffer and not stripped:
                flush_list()
                continue

            if list_buffer:
                flush_list()

            if not stripped:
                flush_paragraph()
                continue

            buffer.append(line)

        if in_code_block:
            flush_code()
        flush_list()
        flush_paragraph()
        return blocks

    def _merge_blocks(self, blocks: list[SectionBlock]) -> list[SectionBlock]:
        """把过短的普通文本块与邻近上下文合并，得到更合理的 chunk。"""
        merged: list[SectionBlock] = []

        for block in blocks:
            if block.block_type in {"code", "image"}:
                if merged and merged[-1].block_type == "paragraph":
                    merged[-1] = SectionBlock(
                        block_type="paragraph",
                        content=f"{merged[-1].content}\n\n{block.content}".strip(),
                    )
                else:
                    merged.append(block)
                continue

            if not merged:
                merged.append(block)
                continue

            previous = merged[-1]
            if self._should_merge(previous, block):
                merged[-1] = SectionBlock(
                    block_type=previous.block_type,
                    content=f"{previous.content}\n\n{block.content}".strip(),
                )
            else:
                merged.append(block)

        return merged

    def _try_ai_regroup_blocks(self, session: Session, blocks: list[SectionBlock]) -> list[SectionBlock] | None:
        """尝试让大模型只做块分组决策，失败时回退本地结果。"""
        if len(blocks) < 3:
            return None

        block_payload = [
            {
                "index": index,
                "block_type": block.block_type,
                "content": block.content,
            }
            for index, block in enumerate(blocks)
        ]
        response = llm_gateway_service.chat_json(
            session,
            "chunking",
            system_prompt=(
                "你是一个 Markdown 知识整理助手。"
                "你不能改写事实，只能基于给定 blocks 判断哪些相邻 blocks 应该合并成同一个 chunk。"
                "请只返回 JSON，对象格式必须为 {\"groups\": [[0], [1, 2]]}。"
            ),
            user_prompt=(
                "请把下面这些按顺序出现的 blocks  regroup 成更适合出题和复习的 chunks。"
                "要求：\n"
                "1. 只能合并相邻 blocks，不能调整顺序。\n"
                "2. 不要遗漏任何 index。\n"
                "3. 尽量让每个 chunk 围绕一个完整小知识点。\n"
                f"4. 原始 blocks JSON 如下：\n{json.dumps(block_payload, ensure_ascii=False)}"
            ),
            temperature=0.1,
        )
        if response is None:
            return None

        groups = response.get("groups")
        if not isinstance(groups, list):
            return None

        regrouped = self._build_blocks_from_groups(blocks, groups)
        return regrouped or None

    def _build_blocks_from_groups(self, blocks: list[SectionBlock], groups: list[object]) -> list[SectionBlock] | None:
        """根据模型返回的相邻分组结果重新构建 blocks。"""
        normalized_groups: list[list[int]] = []
        seen_indexes: list[int] = []

        for group in groups:
            if not isinstance(group, list) or not group:
                return None
            normalized_group: list[int] = []
            for item in group:
                if not isinstance(item, int):
                    return None
                if item < 0 or item >= len(blocks):
                    return None
                normalized_group.append(item)
                seen_indexes.append(item)
            normalized_groups.append(normalized_group)

        if sorted(seen_indexes) != list(range(len(blocks))):
            return None

        regrouped: list[SectionBlock] = []
        for group in normalized_groups:
            if group != list(range(group[0], group[0] + len(group))):
                return None

            grouped_blocks = [blocks[index] for index in group]
            block_type = grouped_blocks[0].block_type
            if any(block.block_type != block_type for block in grouped_blocks):
                block_type = "paragraph"

            regrouped.append(
                SectionBlock(
                    block_type=block_type,
                    content="\n\n".join(block.content for block in grouped_blocks).strip(),
                )
            )

        return regrouped

    def _should_merge(self, previous: SectionBlock, current: SectionBlock) -> bool:
        """判断两个相邻块是否应该合并为同一个 chunk。"""
        if previous.block_type != current.block_type:
            return False

        if previous.block_type in {"ordered_list", "unordered_list"}:
            return True

        compact_previous = re.sub(r"\s+", "", previous.content)
        compact_current = re.sub(r"\s+", "", current.content)
        return len(compact_previous) < 30 or len(compact_current) < 20

    def _detect_list_type(self, line: str) -> str | None:
        """判断某一行是否属于有序或无序列表。"""
        if self.ordered_list_pattern.match(line):
            return "ordered_list"
        if self.unordered_list_pattern.match(line):
            return "unordered_list"
        return None

    def list_chunks(self, session: Session) -> list[KnowledgeChunk]:
        """返回当前系统中的知识点列表。"""
        statement = select(KnowledgeChunk).order_by(KnowledgeChunk.created_at.desc(), KnowledgeChunk.chunk_index.asc())
        return session.exec(statement).all()

    def get_chunk(self, session: Session, chunk_id: int) -> KnowledgeChunk:
        """按 id 返回单个知识点，不存在时抛出业务异常。"""
        chunk = session.get(KnowledgeChunk, chunk_id)
        if chunk is None:
            raise ChunkServiceError("知识点不存在。")
        return chunk


chunk_service = ChunkService()