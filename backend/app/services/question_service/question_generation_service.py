from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session, select

from app.models.entities import Document, KnowledgeChunk, Question, QuestionProgress

from .question_ai_generation_service import question_ai_generation_service
from .question_draft_service import QuestionDraft, question_draft_service
from .question_evidence_service import question_evidence_service


class QuestionServiceError(ValueError):
    """表示题目业务处理中出现的可预期错误。"""


class QuestionDocumentNotFoundError(QuestionServiceError):
    """表示生成题目时目标文档不存在。"""


@dataclass
class QuestionGenerationResult:
    """封装一次题目生成完成后的统计结果。"""

    document_id: int
    chunk_count: int
    generated_question_count: int
    skipped_chunk_count: int


class QuestionGenerationService:
    """负责串联题目生成、去重和入库流程。"""

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
                chunk_type=chunk.chunk_type,
                chunk_summary=chunk.summary,
                chunk_tags=chunk.tags,
                session=session,
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

    def generate_drafts_from_chunk(
        self,
        section_title: str,
        chunk_text: str,
        chunk_type: str | None = None,
        chunk_summary: str | None = None,
        chunk_tags: str | None = None,
        session: Session | None = None,
    ) -> list[QuestionDraft]:
        """基于单个知识点文本生成待入库题目草稿。"""
        normalized_text = chunk_text.strip()
        if not normalized_text:
            return []

        evidence_units = question_evidence_service.extract_evidence_units(normalized_text)
        if not evidence_units:
            return []

        best_evidence = question_evidence_service.choose_best_evidence(evidence_units, chunk_type=chunk_type)
        answer_excerpt = question_draft_service.build_answer_excerpt(
            normalized_text,
            best_evidence,
            chunk_summary=chunk_summary,
        )
        if not question_draft_service.is_usable_source_excerpt(answer_excerpt):
            return []

        local_draft = question_draft_service.build_draft(
            section_title,
            normalized_text,
            best_evidence,
            answer_excerpt,
            chunk_type=chunk_type,
            chunk_summary=chunk_summary,
            chunk_tags=chunk_tags,
        )
        ai_draft = question_ai_generation_service.try_build_ai_draft(
            session=session,
            section_title=section_title,
            chunk_text=normalized_text,
            chunk_type=chunk_type,
            chunk_summary=chunk_summary,
            chunk_tags=chunk_tags,
            evidence=best_evidence,
            answer_excerpt=answer_excerpt,
            fallback_draft=local_draft,
        )
        return [ai_draft or local_draft]

    def _load_existing_question_chunk_ids(self, session: Session, chunk_ids: list[int]) -> set[int]:
        """读取已经生成过题目的知识点 id，用于避免重复生成。"""
        if not chunk_ids:
            return set()

        statement = select(Question.chunk_id).where(Question.chunk_id.in_(chunk_ids))
        return set(session.exec(statement).all())
