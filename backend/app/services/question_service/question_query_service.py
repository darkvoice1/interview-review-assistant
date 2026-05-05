from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlmodel import Session, select

from app.models.entities import Document, KnowledgeChunk, Question, QuestionProgress, ReviewRecord

from .question_generation_service import QuestionServiceError


class QuestionNotFoundError(QuestionServiceError):
    """表示查询题目详情时目标题目不存在。"""


@dataclass
class QuestionListItem:
    """描述题目列表项以及它关联的知识点信息。"""

    question: Question
    document_id: int
    section_title: str
    section_path: str | None


@dataclass
class QuestionDetailItem:
    """描述题目详情以及它关联的上下文和复习状态。"""

    question: Question
    document_id: int
    section_title: str
    section_path: str | None
    source_title: str
    source_type: str
    chunk_content: str
    review_count: int
    correct_streak: int
    mastery_level: int
    last_review_at: datetime | None
    next_review_at: datetime | None
    last_feedback: str | None


@dataclass
class WrongQuestionListItem:
    """描述错题列表项以及它关联的复习状态信息。"""

    question: Question
    document_id: int
    section_title: str
    section_path: str | None
    source_title: str
    last_feedback: str | None
    next_review_at: datetime | None
    review_count: int
    mastery_level: int


class QuestionQueryService:
    """封装题目列表、题目详情和错题查询相关的业务逻辑。"""

    def list_questions(self, session: Session, document_id: int | None = None) -> list[QuestionListItem]:
        """返回题目列表，支持按文档筛选。"""
        statement = (
            select(Question, KnowledgeChunk)
            .join(KnowledgeChunk, KnowledgeChunk.id == Question.chunk_id)
            .order_by(Question.created_at.desc(), Question.id.desc())
        )
        if document_id is not None:
            statement = statement.where(KnowledgeChunk.document_id == document_id)

        rows = session.exec(statement).all()
        return [
            QuestionListItem(
                question=question,
                document_id=chunk.document_id,
                section_title=chunk.section_title,
                section_path=chunk.section_path,
            )
            for question, chunk in rows
        ]

    def get_question(self, session: Session, question_id: int) -> QuestionDetailItem:
        """按 id 返回单个题目的详情信息。"""
        statement = (
            select(Question, KnowledgeChunk, Document, QuestionProgress)
            .join(KnowledgeChunk, KnowledgeChunk.id == Question.chunk_id)
            .join(Document, Document.id == KnowledgeChunk.document_id)
            .join(QuestionProgress, QuestionProgress.question_id == Question.id)
            .where(Question.id == question_id)
        )
        row = session.exec(statement).first()
        if row is None:
            raise QuestionNotFoundError("题目不存在。")

        question, chunk, document, progress = row
        return QuestionDetailItem(
            question=question,
            document_id=chunk.document_id,
            section_title=chunk.section_title,
            section_path=chunk.section_path,
            source_title=document.title,
            source_type=document.source_type,
            chunk_content=chunk.content,
            review_count=progress.review_count,
            correct_streak=progress.correct_streak,
            mastery_level=progress.mastery_level,
            last_review_at=progress.last_review_at,
            next_review_at=progress.next_review_at,
            last_feedback=self._load_latest_feedback(session, question.id),
        )

    def list_wrong_questions(self, session: Session) -> list[WrongQuestionListItem]:
        """返回当前需要重点关注的错题列表。"""
        statement = (
            select(Question, KnowledgeChunk, Document, QuestionProgress)
            .join(KnowledgeChunk, KnowledgeChunk.id == Question.chunk_id)
            .join(Document, Document.id == KnowledgeChunk.document_id)
            .join(QuestionProgress, QuestionProgress.question_id == Question.id)
            .where(QuestionProgress.review_count > 0)
            .where(QuestionProgress.mastery_level < 2)
            .order_by(QuestionProgress.next_review_at.asc(), Question.id.asc())
        )
        rows = session.exec(statement).all()

        items: list[WrongQuestionListItem] = []
        for question, chunk, document, progress in rows:
            items.append(
                WrongQuestionListItem(
                    question=question,
                    document_id=chunk.document_id,
                    section_title=chunk.section_title,
                    section_path=chunk.section_path,
                    source_title=document.title,
                    last_feedback=self._load_latest_feedback(session, question.id),
                    next_review_at=progress.next_review_at,
                    review_count=progress.review_count,
                    mastery_level=progress.mastery_level,
                )
            )

        return items

    def _load_latest_feedback(self, session: Session, question_id: int | None) -> str | None:
        """读取某道题最近一次复习反馈。"""
        if question_id is None:
            return None

        statement = (
            select(ReviewRecord.user_feedback)
            .where(ReviewRecord.question_id == question_id)
            .order_by(ReviewRecord.review_time.desc(), ReviewRecord.id.desc())
        )
        return session.exec(statement).first()