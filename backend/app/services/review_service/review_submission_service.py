from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlmodel import Session, select

from app.core.time_utils import utc_now
from app.models.entities import Question, QuestionProgress, ReviewRecord

from .review_scheduler_service import review_scheduler_service


class ReviewServiceError(ValueError):
    """表示复习业务处理中出现的可预期错误。"""


class ReviewQuestionNotFoundError(ReviewServiceError):
    """表示提交复习时目标题目不存在。"""


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


class ReviewSubmissionService:
    """封装复习反馈提交和进度更新相关的业务逻辑。"""

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

    def submit_review(self, session: Session, question_id: int, user_feedback: str) -> ReviewSubmitResult:
        """保存一次复习反馈，并更新题目的长期进度。"""
        question = session.get(Question, question_id)
        if question is None:
            raise ReviewQuestionNotFoundError("目标题目不存在。")

        progress_statement = select(QuestionProgress).where(QuestionProgress.question_id == question_id)
        progress = session.exec(progress_statement).first()
        if progress is None:
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