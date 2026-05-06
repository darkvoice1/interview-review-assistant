from __future__ import annotations

from .question_draft_service import QuestionDraft
from .question_generation_service import (
    QuestionDocumentNotFoundError,
    QuestionGenerationResult,
    QuestionGenerationService,
    QuestionServiceError,
)
from .question_query_service import (
    QuestionDetailItem,
    QuestionListItem,
    QuestionNotFoundError,
    QuestionQueryService,
    WrongQuestionListItem,
)


class QuestionService(QuestionGenerationService, QuestionQueryService):
    """题目业务门面，统一组合生成和查询能力。"""


question_service = QuestionService()
