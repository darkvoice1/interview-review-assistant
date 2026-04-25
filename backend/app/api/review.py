from datetime import datetime, timedelta

from fastapi import APIRouter

from app.schemas.review import DailyReviewItem, ReviewTodayResponse

# 复习任务相关接口。
router = APIRouter()


@router.get("/today", response_model=ReviewTodayResponse)
def get_today_review() -> ReviewTodayResponse:
    # 这里先生成一份演示题单，后续接真实调度逻辑。
    now = datetime.utcnow()
    items = [
        DailyReviewItem(
            question_id=1,
            question="什么是 Redis 的 AOF 持久化？",
            difficulty=2,
            due_at=now + timedelta(hours=1),
            source_title="Redis Interview Notes",
        )
    ]
    return ReviewTodayResponse(total=len(items), items=items)
