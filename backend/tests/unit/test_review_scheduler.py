from datetime import datetime

from app.services.review_scheduler import ReviewSchedulerService


def test_next_review_at_uses_expected_intervals() -> None:
    """调度器应按当前 MVP 规则返回固定间隔。"""
    scheduler = ReviewSchedulerService()
    base_time = datetime(2026, 1, 1, 9, 0, 0)

    assert scheduler.next_review_at("不会", base_time) == datetime(2026, 1, 2, 9, 0, 0)
    assert scheduler.next_review_at("模糊", base_time) == datetime(2026, 1, 3, 9, 0, 0)
    assert scheduler.next_review_at("会", base_time) == datetime(2026, 1, 6, 9, 0, 0)
    assert scheduler.next_review_at("未知", base_time) == datetime(2026, 1, 2, 9, 0, 0)