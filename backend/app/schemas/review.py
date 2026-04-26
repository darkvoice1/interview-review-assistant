from datetime import datetime

from pydantic import BaseModel


# 单条今日复习题目。
class DailyReviewItem(BaseModel):
    """描述今日题单中的单条复习题目。"""

    question_id: int
    question: str
    difficulty: int
    due_at: datetime
    source_title: str


# 今日题单的整体返回结构。
class ReviewTodayResponse(BaseModel):
    """描述今日题单接口返回的整体数据结构。"""

    total: int
    items: list[DailyReviewItem]