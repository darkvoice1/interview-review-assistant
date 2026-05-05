from __future__ import annotations

from .review_query_service import ReviewQueryService, ReviewStatsResult, ReviewTodayListItem
from .review_submission_service import (
    ReviewQuestionNotFoundError,
    ReviewServiceError,
    ReviewSubmissionService,
    ReviewSubmitResult,
)


class ReviewService(ReviewQueryService, ReviewSubmissionService):
    """复习业务门面，统一组合查询、提交和调度相关能力。"""


review_service = ReviewService()