from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.review import DailyReviewItem, ReviewSubmitRequest, ReviewSubmitResponse, ReviewTodayResponse
from app.services.review_service import ReviewQuestionNotFoundError, ReviewServiceError, review_service

# 复习任务相关接口。
router = APIRouter()


@router.get("/today", response_model=ReviewTodayResponse)
def get_today_review(session: Session = Depends(get_session)) -> ReviewTodayResponse:
    """返回当前系统中的真实今日待复习题单。"""
    items = review_service.list_today_reviews(session)
    return ReviewTodayResponse(
        total=len(items),
        items=[
            DailyReviewItem(
                question_id=item.question_id,
                question=item.question,
                difficulty=item.difficulty,
                due_at=item.due_at,
                source_title=item.source_title,
            )
            for item in items
        ],
    )


@router.post("/submit", response_model=ReviewSubmitResponse)
def submit_review(payload: ReviewSubmitRequest, session: Session = Depends(get_session)) -> ReviewSubmitResponse:
    """提交一次题目复习反馈，并更新下次复习时间。"""
    try:
        result = review_service.submit_review(
            session,
            question_id=payload.question_id,
            user_feedback=payload.user_feedback,
        )
    except ReviewQuestionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReviewServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ReviewSubmitResponse(
        question_id=result.question_id,
        user_feedback=result.user_feedback,
        review_time=result.review_time,
        next_review_at=result.next_review_at,
        review_count=result.review_count,
        correct_streak=result.correct_streak,
        mastery_level=result.mastery_level,
    )
