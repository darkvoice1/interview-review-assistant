from datetime import datetime
from typing import Literal

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


# 提交复习反馈时的请求体。
class ReviewSubmitRequest(BaseModel):
    """描述一次题目复习提交需要的字段。"""

    question_id: int
    user_feedback: Literal["不会", "模糊", "会"]


# 提交复习反馈后的返回结构。
class ReviewSubmitResponse(BaseModel):
    """描述复习提交完成后返回给前端的结果。"""

    question_id: int
    user_feedback: Literal["不会", "模糊", "会"]
    review_time: datetime
    next_review_at: datetime
    review_count: int
    correct_streak: int
    mastery_level: int
