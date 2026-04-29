from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.time_utils import utc_now
from app.models.entities import Document, KnowledgeChunk, Question, QuestionProgress


@dataclass
class ReviewTodayListItem:
    """描述今日题单中的单条复习项。"""

    question_id: int
    question: str
    difficulty: int
    due_at: datetime
    source_title: str
    is_new: bool


# 复习服务，负责组装今日题单等复习相关业务逻辑。
class ReviewService:
    """封装今日题单查询等复习模块业务逻辑。"""

    def list_today_reviews(self, session: Session, current_time: datetime | None = None) -> list[ReviewTodayListItem]:
        """返回当前时间点应该进入今日题单的题目。"""
        now = current_time or utc_now()

        # 新题 next_review_at 为空，已到期题目则 next_review_at 小于等于当前时间。
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

        # 先展示已到期题，再展示新题，保证今日题单更贴近复习优先级。
        items.sort(
            key=lambda item: (
                1 if item.is_new else 0,
                item.due_at,
                item.question_id,
            )
        )
        return items


review_service = ReviewService()
