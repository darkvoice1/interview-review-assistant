from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.review import DailyReviewItem, ReviewTodayResponse
from app.services.review_service import review_service

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
