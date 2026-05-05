from datetime import datetime, timedelta

from app.core.time_utils import utc_now


class ReviewSchedulerService:
    """根据用户反馈计算题目的下次复习时间。"""

    intervals = {
        "不会": 1,
        "模糊": 2,
        "会": 5,
    }

    def next_review_at(self, feedback: str, base_time: datetime | None = None) -> datetime:
        """按当前简化规则返回下次复习时间。"""
        now = base_time or utc_now()
        days = self.intervals.get(feedback, 1)
        return now + timedelta(days=days)


review_scheduler_service = ReviewSchedulerService()