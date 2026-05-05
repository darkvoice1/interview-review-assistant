from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.time_utils import utc_now
from app.models.entities import Document, KnowledgeChunk, Question, QuestionProgress, ReviewRecord

from .review_submission_service import ReviewServiceError


@dataclass
class ReviewTodayListItem:
    """描述今日题单中的单条复习项。"""

    question_id: int
    question: str
    difficulty: int
    due_at: datetime
    source_title: str
    is_new: bool


@dataclass
class ReviewStatsResult:
    """描述最小版复习统计结果。"""

    document_count: int
    question_count: int
    due_review_count: int
    wrong_question_count: int
    review_record_count: int
    reviewed_today_count: int


class ReviewQueryService:
    """封装今日题单和复习统计查询相关的业务逻辑。"""

    def list_today_reviews(self, session: Session, current_time: datetime | None = None) -> list[ReviewTodayListItem]:
        """返回当前时间点应该进入今日题单的题目。"""
        now = current_time or utc_now()

        statement = (
            select(Question, QuestionProgress, Document)
            .join(QuestionProgress, QuestionProgress.question_id == Question.id)
            .join(KnowledgeChunk, KnowledgeChunk.id == Question.chunk_id)
            .join(Document, Document.id == KnowledgeChunk.document_id)
            .where(
                or_(
                    QuestionProgress.next_review_at.is_(None),
                    QuestionProgress.next_review_at <= now,
                )
            )
        )
        rows = session.exec(statement).all()

        items = [
            ReviewTodayListItem(
                question_id=question.id,
                question=question.question,
                difficulty=question.difficulty,
                due_at=progress.next_review_at or question.created_at,
                source_title=document.title,
                is_new=progress.next_review_at is None,
            )
            for question, progress, document in rows
            if question.id is not None
        ]

        items.sort(
            key=lambda item: (
                1 if item.is_new else 0,
                item.due_at,
                item.question_id,
            )
        )
        return items

    def get_stats(self, session: Session, current_time: datetime | None = None) -> ReviewStatsResult:
        """返回最小版复习统计数据。"""
        now = current_time or utc_now()
        today = now.date()

        document_count = len(session.exec(select(Document.id)).all())
        question_count = len(session.exec(select(Question.id)).all())
        review_record_count = len(session.exec(select(ReviewRecord.id)).all())

        due_statement = (
            select(QuestionProgress.id)
            .where(
                or_(
                    QuestionProgress.next_review_at.is_(None),
                    QuestionProgress.next_review_at <= now,
                )
            )
        )
        due_review_count = len(session.exec(due_statement).all())

        wrong_statement = (
            select(QuestionProgress.id)
            .where(QuestionProgress.review_count > 0)
            .where(QuestionProgress.mastery_level < 2)
        )
        wrong_question_count = len(session.exec(wrong_statement).all())

        reviewed_today_count = len(
            [
                record_id
                for record_id in session.exec(select(ReviewRecord.id, ReviewRecord.review_time)).all()
                if record_id[1].date() == today
            ]
        )

        return ReviewStatsResult(
            document_count=document_count,
            question_count=question_count,
            due_review_count=due_review_count,
            wrong_question_count=wrong_question_count,
            review_record_count=review_record_count,
            reviewed_today_count=reviewed_today_count,
        )