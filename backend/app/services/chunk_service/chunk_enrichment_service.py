from __future__ import annotations

import json
import re

from sqlmodel import Session

from app.services.llm_service import llm_gateway_service

from .chunk_models import SectionBlock


class ChunkEnrichmentService:
    """负责基于大模型对 chunk 做 regroup 与元信息增强。"""

    chunk_type_pattern = re.compile(r"^[a-z_]{1,40}$")

    def try_ai_regroup_blocks(self, session: Session, blocks: list[SectionBlock]) -> list[SectionBlock] | None:
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
                "请把下面这些按顺序出现的 blocks regroup 成更适合出题和复习的 chunks。"
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

        regrouped = self.build_blocks_from_groups(blocks, groups)
        return regrouped or None

    def try_ai_enrich_blocks(
        self,
        session: Session,
        section: dict,
        blocks: list[SectionBlock],
    ) -> list[SectionBlock] | None:
        """尝试让大模型判断 chunk 是否保留并补充元信息，失败时回退本地结果。"""
        if not blocks:
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
                "你不能改写原文事实，也不能输出原文中不存在的新知识。"
                "你只能基于给定 section 和 chunks，判断每个 chunk 是否值得保留，并补充简短元信息。"
                "请只返回 JSON，对象格式必须为 "
                "{\"chunks\": [{\"index\": 0, \"keep\": true, \"chunk_type\": \"definition\", \"summary\": \"...\", \"tags\": [\"...\"]}]}。"
            ),
            user_prompt=(
                f"section_title: {section['section_title']}\n"
                f"section_path: {section.get('section_path') or section['section_title']}\n"
                "请逐个判断下面这些 chunks 是否值得保留为后续复习知识点。\n"
                "要求：\n"
                "1. 每个 index 都必须返回一次，不能遗漏。\n"
                "2. keep=false 只用于明显没有独立复习价值的过渡性、噪声性内容。\n"
                "3. chunk_type 可以在原 block_type 基础上提升为更语义化的类型，比如 definition、comparison、process、scenario，但不要随意发明。\n"
                "4. summary 要非常简短，只概括当前 chunk 在讲什么。\n"
                "5. tags 返回 0 到 5 个短标签。\n"
                f"6. 原始 chunks JSON 如下：\n{json.dumps(block_payload, ensure_ascii=False)}"
            ),
            temperature=0.1,
        )
        if response is None:
            return None

        items = response.get("chunks")
        if not isinstance(items, list):
            return None

        enhanced = self.build_blocks_from_ai_metadata(blocks, items)
        return enhanced or None

    def build_blocks_from_ai_metadata(self, blocks: list[SectionBlock], items: list[object]) -> list[SectionBlock] | None:
        """根据模型返回的 metadata 构建增强后的 blocks。"""
        if len(items) != len(blocks):
            return None

        metadata_by_index: dict[int, dict] = {}
        for item in items:
            if not isinstance(item, dict):
                return None
            index = item.get("index")
            if not isinstance(index, int):
                return None
            if index < 0 or index >= len(blocks) or index in metadata_by_index:
                return None
            metadata_by_index[index] = item

        if sorted(metadata_by_index) != list(range(len(blocks))):
            return None

        enhanced: list[SectionBlock] = []
        for index, block in enumerate(blocks):
            item = metadata_by_index[index]
            keep = item.get("keep")
            if not isinstance(keep, bool):
                return None
            if not keep:
                continue

            enhanced.append(
                SectionBlock(
                    block_type=self.normalize_ai_chunk_type(item.get("chunk_type"), block.block_type),
                    content=block.content,
                    summary=self.normalize_ai_summary(item.get("summary")),
                    tags=self.normalize_ai_tags(item.get("tags")),
                )
            )

        return enhanced or None

    def build_blocks_from_groups(self, blocks: list[SectionBlock], groups: list[object]) -> list[SectionBlock] | None:
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

    def normalize_ai_chunk_type(self, value: object, fallback: str) -> str:
        """规范化模型返回的 chunk_type，异常时回退到原始类型。"""
        if not isinstance(value, str):
            return fallback

        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        if not normalized:
            return fallback
        if normalized == "list":
            return fallback if fallback in {"ordered_list", "unordered_list"} else "paragraph"
        if not self.chunk_type_pattern.fullmatch(normalized):
            return fallback
        return normalized

    def normalize_ai_summary(self, value: object) -> str | None:
        """规范化模型返回的 summary。"""
        if not isinstance(value, str):
            return None

        summary = re.sub(r"\s+", " ", value).strip()
        if not summary:
            return None
        return summary[:120]

    def normalize_ai_tags(self, value: object) -> list[str] | None:
        """规范化模型返回的 tags。"""
        if not isinstance(value, list):
            return None

        tags: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            tag = re.sub(r"\s+", " ", item).strip()
            if not tag or len(tag) > 24 or tag in tags:
                continue
            tags.append(tag)
            if len(tags) >= 5:
                break

        return tags or None

    def join_tags(self, tags: list[str] | None) -> str | None:
        """把标签列表转换成入库用的逗号分隔字符串。"""
        if not tags:
            return None
        return ",".join(tags)


chunk_enrichment_service = ChunkEnrichmentService()
