from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.time_utils import utc_now
from app.models.entities import Document, KnowledgeChunk, Question, QuestionProgress, ReviewRecord
from app.services.review_scheduler import review_scheduler_service


class ReviewServiceError(ValueError):
    """表示复习业务处理中出现的可预期错误。"""

    pass


class ReviewQuestionNotFoundError(ReviewServiceError):
    """表示提交复习时目标题目不存在。"""

    pass


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
class ReviewSubmitResult:
    """描述一次复习反馈提交完成后的结果。"""

    question_id: int
    user_feedback: str
    review_time: datetime
    next_review_at: datetime
    review_count: int
    correct_streak: int
    mastery_level: int


# 复习服务，负责组装今日题单等复习相关业务逻辑。
class ReviewService:
    """封装今日题单查询和复习反馈提交等业务逻辑。"""

    quality_scores = {
        "不会": 0,
        "模糊": 1,
        "会": 2,
    }

    mastery_levels = {
        "不会": 0,
        "模糊": 1,
        "会": 2,
    }

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

    def submit_review(self, session: Session, question_id: int, user_feedback: str) -> ReviewSubmitResult:
        """保存一次复习反馈，并更新题目的长期进度。"""
        question = session.get(Question, question_id)
        if question is None:
            raise ReviewQuestionNotFoundError("目标题目不存在。")

        progress_statement = select(QuestionProgress).where(QuestionProgress.question_id == question_id)
        progress = session.exec(progress_statement).first()
        if progress is None:
            # 正常情况下题目生成时就会初始化进度，这里做一层兜底。
            progress = QuestionProgress(question_id=question_id)
            session.add(progress)
            session.flush()

        review_time = utc_now()
        next_review_at = review_scheduler_service.next_review_at(user_feedback, base_time=review_time)

        record = ReviewRecord(
            question_id=question_id,
            review_time=review_time,
            user_feedback=user_feedback,
            quality_score=self.quality_scores[user_feedback],
            next_review_at=next_review_at,
        )
        session.add(record)

        progress.review_count += 1
        progress.last_review_at = review_time
        progress.next_review_at = next_review_at
        progress.correct_streak = progress.correct_streak + 1 if user_feedback == "会" else 0
        progress.mastery_level = self.mastery_levels[user_feedback]

        session.commit()
        return ReviewSubmitResult(
            question_id=question_id,
            user_feedback=user_feedback,
            review_time=review_time,
            next_review_at=next_review_at,
            review_count=progress.review_count,
            correct_streak=progress.correct_streak,
            mastery_level=progress.mastery_level,
        )


review_service = ReviewService()
