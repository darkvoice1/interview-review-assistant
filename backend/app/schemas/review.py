from datetime import datetime

from pydantic import BaseModel


# 单条今日复习题目。
class DailyReviewItem(BaseModel):
    question_id: int
    question: str
    difficulty: int
    due_at: datetime
    source_title: str


# 今日题单的整体返回结构。
class ReviewTodayResponse(BaseModel):
    total: int
    items: list[DailyReviewItem]
