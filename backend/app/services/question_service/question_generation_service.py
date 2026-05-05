from __future__ import annotations

import re
from dataclasses import dataclass

from sqlmodel import Session, select

from app.models.entities import Document, KnowledgeChunk, Question, QuestionProgress


class QuestionServiceError(ValueError):
    """表示题目业务处理中出现的可预期错误。"""


class QuestionDocumentNotFoundError(QuestionServiceError):
    """表示生成题目时目标文档不存在。"""


@dataclass
class QuestionEvidenceUnit:
    """描述一条可直接支撑出题的原文证据单元。"""

    kind: str
    text: str
    index: int
    start: int
    end: int


@dataclass
class QuestionDraft:
    """描述规则生成器产出的一道待入库题目。"""

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


@dataclass
class QuestionGenerationResult:
    """封装一次题目生成完成后的统计结果。"""

    document_id: int
    chunk_count: int
    generated_question_count: int
    skipped_chunk_count: int


class QuestionGenerationService:
    """封装题目生成、去重保存相关的业务逻辑。"""

    split_pattern = re.compile(r"(?<=[。！？；;])\s*|\n+")
    bullet_prefix_pattern = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)?]\s*)")

    comparison_keywords = ("区别", "不同", "相比", "对比", "异同", "相同")
    pros_cons_keywords = ("优缺点", "优点", "缺点", "优势", "劣势")
    process_keywords = ("步骤", "流程", "过程", "首先", "然后", "最后", "第一", "第二", "第三")
    reason_keywords = ("原因", "为什么", "因为", "目的", "作用", "意义")
    scenario_keywords = ("比如", "例如", "场景", "适用于", "适合", "实践中", "面试中")
    definition_pattern = re.compile(r"^[^。！？；;]{0,24}(?:是|指|表示|用于|用来|负责)")

    def generate_questions_for_document(self, session: Session, document_id: int) -> QuestionGenerationResult:
        """为指定文档的知识点批量生成基础题目。"""
        document = session.get(Document, document_id)
        if document is None:
            raise QuestionDocumentNotFoundError("目标文档不存在。")

        chunk_statement = (
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.id)
        )
        chunks = session.exec(chunk_statement).all()
        if not chunks:
            raise QuestionServiceError("当前文档还没有可生成题目的知识点。")

        chunk_ids = [chunk.id for chunk in chunks if chunk.id is not None]
        existing_chunk_ids = self._load_existing_question_chunk_ids(session, chunk_ids)

        questions_to_create: list[Question] = []
        skipped_chunk_count = 0

        for chunk in chunks:
            if chunk.id is None:
                continue

            if chunk.id in existing_chunk_ids:
                skipped_chunk_count += 1
                continue

            drafts = self.generate_drafts_from_chunk(
                section_title=chunk.section_title,
                chunk_text=chunk.content,
            )
            for draft in drafts:
                questions_to_create.append(
                    Question(
                        chunk_id=chunk.id,
                        question_type=draft.question_type,
                        question=draft.question,
                        answer=draft.answer,
                        source_excerpt=draft.source_excerpt,
                        evidence_kind=draft.evidence_kind,
                        evidence_index=draft.evidence_index,
                        evidence_start=draft.evidence_start,
                        evidence_end=draft.evidence_end,
                        analysis=draft.analysis,
                        difficulty=draft.difficulty,
                    )
                )

        for question in questions_to_create:
            session.add(question)

        session.flush()

        for question in questions_to_create:
            if question.id is None:
                continue
            session.add(QuestionProgress(question_id=question.id))

        session.commit()
        return QuestionGenerationResult(
            document_id=document_id,
            chunk_count=len(chunks),
            generated_question_count=len(questions_to_create),
            skipped_chunk_count=skipped_chunk_count,
        )

    def generate_drafts_from_chunk(self, section_title: str, chunk_text: str) -> list[QuestionDraft]:
        """基于单个知识点文本生成待入库题目草稿。"""
        normalized_text = chunk_text.strip()
        if not normalized_text:
            return []

        evidence_units = self._extract_evidence_units(normalized_text)
        if not evidence_units:
            return []

        best_evidence = self._choose_best_evidence(evidence_units)
        answer_excerpt = self._build_answer_excerpt(normalized_text, best_evidence)
        if not self._is_usable_source_excerpt(answer_excerpt):
            return []

        return [self._build_draft(section_title, normalized_text, best_evidence, answer_excerpt)]

    def _extract_evidence_units(self, chunk_text: str) -> list[QuestionEvidenceUnit]:
        """把正文提取成可出题的结构化原文证据单元。"""
        units: list[QuestionEvidenceUnit] = []
        search_start = 0

        for index, raw_unit in enumerate(self._split_text_units(chunk_text)):
            start = chunk_text.find(raw_unit, search_start)
            if start == -1:
                start = chunk_text.find(raw_unit)
            if start == -1:
                start = 0
            end = start + len(raw_unit)
            search_start = end

            evidence_kind = self._classify_unit_kind(raw_unit)
            units.append(
                QuestionEvidenceUnit(
                    kind=evidence_kind,
                    text=raw_unit,
                    index=index,
                    start=start,
                    end=end,
                )
            )

        return units

    def _choose_best_evidence(self, evidence_units: list[QuestionEvidenceUnit]) -> QuestionEvidenceUnit:
        """按优先级挑选最适合作为当前题目依据的证据单元。"""
        priority_order = {
            "pros_cons": 0,
            "comparison": 1,
            "process": 2,
            "reason": 3,
            "scenario": 4,
            "definition": 5,
            "summary": 6,
        }
        return min(
            evidence_units,
            key=lambda unit: (priority_order.get(unit.kind, 99), unit.index),
        )

    def _build_draft(
        self,
        section_title: str,
        normalized_text: str,
        evidence: QuestionEvidenceUnit,
        answer_excerpt: str,
    ) -> QuestionDraft:
        """根据证据单元和题型模板生成一条题目草稿。"""
        if evidence.kind == "definition":
            return QuestionDraft(
                question_type="definition_short_answer",
                question=f"什么是 {section_title}？",
                answer=answer_excerpt,
                source_excerpt=answer_excerpt,
                evidence_kind=evidence.kind,
                evidence_index=evidence.index,
                evidence_start=evidence.start,
                evidence_end=evidence.end,
                analysis="这道题用于检查你是否能准确说出该知识点的定义或本质。",
                difficulty=1,
            )

        if evidence.kind == "comparison":
            return QuestionDraft(
                question_type="comparison_short_answer",
                question=f"{section_title} 中有哪些关键区别或对比点？",
                answer=answer_excerpt,
                source_excerpt=answer_excerpt,
                evidence_kind=evidence.kind,
                evidence_index=evidence.index,
                evidence_start=evidence.start,
                evidence_end=evidence.end,
                analysis="这道题用于检查你是否能回忆该知识点中的对比关系和差异点。",
                difficulty=2,
            )

        if evidence.kind == "pros_cons":
            return QuestionDraft(
                question_type="pros_cons_short_answer",
                question=f"{section_title} 的优点和缺点分别是什么？",
                answer=answer_excerpt,
                source_excerpt=answer_excerpt,
                evidence_kind=evidence.kind,
                evidence_index=evidence.index,
                evidence_start=evidence.start,
                evidence_end=evidence.end,
                analysis="这道题用于检查你是否能总结该方案的优缺点与取舍。",
                difficulty=2,
            )

        if evidence.kind == "process":
            return QuestionDraft(
                question_type="process_short_answer",
                question=f"{section_title} 的关键步骤是什么？",
                answer=answer_excerpt,
                source_excerpt=answer_excerpt,
                evidence_kind=evidence.kind,
                evidence_index=evidence.index,
                evidence_start=evidence.start,
                evidence_end=evidence.end,
                analysis="这道题用于检查你是否能按顺序回忆该知识点的流程或步骤。",
                difficulty=2,
            )

        if evidence.kind == "reason":
            return QuestionDraft(
                question_type="reason_short_answer",
                question=f"{section_title} 的原因、目的或作用是什么？",
                answer=answer_excerpt,
                source_excerpt=answer_excerpt,
                evidence_kind=evidence.kind,
                evidence_index=evidence.index,
                evidence_start=evidence.start,
                evidence_end=evidence.end,
                analysis="这道题用于检查你是否能解释该知识点背后的原因、目的或意义。",
                difficulty=2,
            )

        if evidence.kind == "scenario":
            return QuestionDraft(
                question_type="scenario_short_answer",
                question=f"{section_title} 更适用于什么场景？",
                answer=answer_excerpt,
                source_excerpt=answer_excerpt,
                evidence_kind=evidence.kind,
                evidence_index=evidence.index,
                evidence_start=evidence.start,
                evidence_end=evidence.end,
                analysis="这道题用于检查你是否能结合原文回忆该知识点适用的典型场景。",
                difficulty=2,
            )

        return QuestionDraft(
            question_type="summary_short_answer",
            question=f"{section_title} 的核心内容是什么？",
            answer=answer_excerpt,
            source_excerpt=answer_excerpt,
            evidence_kind=evidence.kind,
            evidence_index=evidence.index,
            evidence_start=evidence.start,
            evidence_end=evidence.end,
            analysis="这道题用于检查你是否能根据标题回忆该知识点的核心内容。",
            difficulty=1,
        )

    def _classify_unit_kind(self, unit: str) -> str:
        """判断某条证据单元更适合归为哪类题型。"""
        if self._looks_like_pros_cons(unit):
            return "pros_cons"
        if self._looks_like_comparison(unit):
            return "comparison"
        if self._looks_like_process(unit):
            return "process"
        if self._looks_like_reason(unit):
            return "reason"
        if self._looks_like_scenario(unit):
            return "scenario"
        if self._looks_like_definition(unit):
            return "definition"
        return "summary"

    def _split_text_units(self, chunk_text: str) -> list[str]:
        """把正文拆成更容易识别的句子或要点单元。"""
        units: list[str] = []
        for raw_unit in self.split_pattern.split(chunk_text):
            cleaned_unit = self.bullet_prefix_pattern.sub("", raw_unit.strip())
            if cleaned_unit:
                units.append(cleaned_unit)
        return units

    def _looks_like_definition(self, unit: str) -> bool:
        """判断某段文本是否更像定义句。"""
        compact_unit = unit.strip()
        if len(compact_unit) < 6:
            return False
        return self.definition_pattern.search(compact_unit) is not None

    def _looks_like_comparison(self, unit: str) -> bool:
        """判断某段文本是否更像对比句。"""
        return any(keyword in unit for keyword in self.comparison_keywords)

    def _looks_like_pros_cons(self, unit: str) -> bool:
        """判断某段文本是否更像优缺点句。"""
        return any(keyword in unit for keyword in self.pros_cons_keywords)

    def _looks_like_process(self, unit: str) -> bool:
        """判断某段文本是否更像流程步骤句。"""
        return any(keyword in unit for keyword in self.process_keywords)

    def _looks_like_reason(self, unit: str) -> bool:
        """判断某段文本是否更像原因或目的句。"""
        return any(keyword in unit for keyword in self.reason_keywords)

    def _looks_like_scenario(self, unit: str) -> bool:
        """判断某段文本是否更像场景句。"""
        return any(keyword in unit for keyword in self.scenario_keywords)

    def _build_answer_excerpt(self, normalized_text: str, evidence: QuestionEvidenceUnit) -> str:
        """优先返回贴近原文证据的答案摘要。"""
        if len(evidence.text) >= 12:
            return evidence.text
        if len(normalized_text) <= 160:
            return normalized_text
        return normalized_text[:160]

    def _is_usable_source_excerpt(self, source_excerpt: str) -> bool:
        """过滤掉过短、几乎无法支撑题目的原文证据。"""
        compact_excerpt = re.sub(r"\s+", "", source_excerpt)
        return len(compact_excerpt) >= 6

    def _load_existing_question_chunk_ids(self, session: Session, chunk_ids: list[int]) -> set[int]:
        """读取已经生成过题目的知识点 id，用于避免重复生成。"""
        if not chunk_ids:
            return set()

        statement = select(Question.chunk_id).where(Question.chunk_id.in_(chunk_ids))
        return set(session.exec(statement).all())