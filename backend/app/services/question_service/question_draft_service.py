from __future__ import annotations

import re
from dataclasses import dataclass

from .question_evidence_service import QuestionEvidenceUnit


@dataclass
class QuestionDraft:
    """描述一条由规则或 AI 润色后得到的题目草稿。"""

    question_type: str
    question: str
    answer: str
    source_excerpt: str | None = None
    evidence_kind: str | None = None
    evidence_index: int | None = None
    evidence_start: int | None = None
    evidence_end: int | None = None
    analysis: str | None = None
    difficulty: int = 1


class QuestionDraftService:
    """负责根据证据和 chunk 元信息组装题目草稿。"""

    def build_draft(
        self,
        section_title: str,
        normalized_text: str,
        evidence: QuestionEvidenceUnit,
        answer_excerpt: str,
        chunk_type: str | None = None,
        chunk_summary: str | None = None,
        chunk_tags: str | None = None,
    ) -> QuestionDraft:
        """根据证据单元和题型模板生成一条题目草稿。"""
        prompt_subject = self._build_question_subject(section_title, chunk_summary=chunk_summary)
        answer_with_context = self._build_answer_with_context(
            answer_excerpt,
            chunk_summary=chunk_summary,
            chunk_tags=chunk_tags,
        )

        if evidence.kind == "definition":
            return QuestionDraft(
                question_type="definition_short_answer",
                question='什么是' + " " + prompt_subject + '？',
                answer=answer_with_context,
                source_excerpt=answer_excerpt,
                evidence_kind=evidence.kind,
                evidence_index=evidence.index,
                evidence_start=evidence.start,
                evidence_end=evidence.end,
                analysis='这道题用于检查你是否能准确说出该知识点的定义或本质。',
                difficulty=1,
            )

        if evidence.kind == "comparison":
            return QuestionDraft(
                question_type="comparison_short_answer",
                question=prompt_subject + ' 中有哪些关键区别或对比点？',
                answer=answer_with_context,
                source_excerpt=answer_excerpt,
                evidence_kind=evidence.kind,
                evidence_index=evidence.index,
                evidence_start=evidence.start,
                evidence_end=evidence.end,
                analysis='这道题用于检查你是否能回忆该知识点中的对比关系和差异点。',
                difficulty=2,
            )

        if evidence.kind == "pros_cons":
            return QuestionDraft(
                question_type="pros_cons_short_answer",
                question=prompt_subject + ' 的优点和缺点分别是什么？',
                answer=answer_with_context,
                source_excerpt=answer_excerpt,
                evidence_kind=evidence.kind,
                evidence_index=evidence.index,
                evidence_start=evidence.start,
                evidence_end=evidence.end,
                analysis='这道题用于检查你是否能总结该方案的优缺点与取舍。',
                difficulty=2,
            )

        if evidence.kind == "process":
            return QuestionDraft(
                question_type="process_short_answer",
                question=prompt_subject + ' 的关键步骤是什么？',
                answer=answer_with_context,
                source_excerpt=answer_excerpt,
                evidence_kind=evidence.kind,
                evidence_index=evidence.index,
                evidence_start=evidence.start,
                evidence_end=evidence.end,
                analysis='这道题用于检查你是否能按顺序回忆该知识点的流程或步骤。',
                difficulty=2,
            )

        if evidence.kind == "reason":
            return QuestionDraft(
                question_type="reason_short_answer",
                question=prompt_subject + ' 的原因、目的或作用是什么？',
                answer=answer_with_context,
                source_excerpt=answer_excerpt,
                evidence_kind=evidence.kind,
                evidence_index=evidence.index,
                evidence_start=evidence.start,
                evidence_end=evidence.end,
                analysis='这道题用于检查你是否能解释该知识点背后的原因、目的或意义。',
                difficulty=2,
            )

        if evidence.kind == "scenario":
            return QuestionDraft(
                question_type="scenario_short_answer",
                question=prompt_subject + ' 更适用于什么场景？',
                answer=answer_with_context,
                source_excerpt=answer_excerpt,
                evidence_kind=evidence.kind,
                evidence_index=evidence.index,
                evidence_start=evidence.start,
                evidence_end=evidence.end,
                analysis='这道题用于检查你是否能结合原文回忆该知识点适用的典型场景。',
                difficulty=2,
            )

        return QuestionDraft(
            question_type="summary_short_answer",
            question=prompt_subject + ' 的核心内容是什么？',
            answer=answer_with_context,
            source_excerpt=answer_excerpt,
            evidence_kind=evidence.kind,
            evidence_index=evidence.index,
            evidence_start=evidence.start,
            evidence_end=evidence.end,
            analysis='这道题用于检查你是否能根据标题回忆该知识点的核心内容。',
            difficulty=1,
        )

    def build_answer_excerpt(
        self,
        normalized_text: str,
        evidence: QuestionEvidenceUnit,
        chunk_summary: str | None = None,
    ) -> str:
        """优先返回贴近原文证据的答案摘要。"""
        if len(evidence.text) >= 12:
            return evidence.text
        if chunk_summary:
            summary = chunk_summary.strip()
            if len(summary) >= 8:
                return summary
        if len(normalized_text) <= 160:
            return normalized_text
        return normalized_text[:160]

    def is_usable_source_excerpt(self, source_excerpt: str) -> bool:
        """过滤掉过短、几乎无法支撑题目的原文证据。"""
        compact_excerpt = re.sub(r"\s+", "", source_excerpt)
        return len(compact_excerpt) >= 6

    def _build_question_subject(self, section_title: str, chunk_summary: str | None = None) -> str:
        """根据 section 标题和 chunk 摘要生成更自然的题目主语。"""
        summary = (chunk_summary or "").strip()
        if not summary:
            return section_title
        if summary == section_title:
            return section_title
        return section_title + '（' + summary + '）'

    def _build_answer_with_context(
        self,
        answer_excerpt: str,
        chunk_summary: str | None = None,
        chunk_tags: str | None = None,
    ) -> str:
        """在不改写事实的前提下，为答案补充简短上下文。"""
        lines: list[str] = []
        summary = (chunk_summary or "").strip()
        tags = self._split_tags(chunk_tags)
        if summary:
            lines.append('知识点摘要：' + summary)
        if tags:
            lines.append('关联标签：' + '、'.join(tags))
        lines.append(answer_excerpt)
        return "\n".join(lines)

    def _split_tags(self, chunk_tags: str | None) -> list[str]:
        """把入库后的标签字符串拆回列表。"""
        if not chunk_tags:
            return []
        return [item.strip() for item in chunk_tags.split(",") if item.strip()]


question_draft_service = QuestionDraftService()
