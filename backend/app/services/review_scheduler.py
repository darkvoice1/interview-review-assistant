from datetime import datetime, timedelta


# 复习调度服务，负责计算下次复习时间。
class ReviewSchedulerService:
    # 第一版先使用固定间隔规则。
    intervals = {
        "不会": 1,
        "模糊": 2,
        "会": 5,
    }

    def next_review_at(self, feedback: str, base_time: datetime | None = None) -> datetime:
        # 如果外部没传时间，就默认以当前时间为基准。
        now = base_time or datetime.utcnow()
        days = self.intervals.get(feedback, 1)
        return now + timedelta(days=days)
