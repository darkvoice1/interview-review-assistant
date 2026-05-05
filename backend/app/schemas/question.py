from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class QuestionRead(BaseModel):
    """描述题目列表返回给前端时的完整字段。"""

    id: int
    chunk_id: int
    document_id: int
    section_title: str
    section_path: Optional[str] = None
    question_type: str
    question: str
    answer: str
    source_excerpt: Optional[str] = None
    evidence_kind: Optional[str] = None
    evidence_index: Optional[int] = None
    evidence_start: Optional[int] = None
    evidence_end: Optional[int] = None
    analysis: Optional[str] = None
    difficulty: int
    created_at: datetime


class QuestionDetailRead(QuestionRead):
    """描述题目详情以及它关联的原文上下文和复习状态。"""

    source_title: str
    source_type: str
    chunk_content: str
    review_count: int
    correct_streak: int
    mastery_level: int
    last_review_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    last_feedback: Optional[str] = None


class WrongQuestionRead(QuestionRead):
    """描述错题列表项以及它关联的复习状态字段。"""

    source_title: str
    last_feedback: Optional[str] = None
    next_review_at: Optional[datetime] = None
    review_count: int
    mastery_level: int


class QuestionGenerateResult(BaseModel):
    """描述一次批量生成题目后的统计结果。"""

    document_id: int
    chunk_count: int
    generated_question_count: int
    skipped_chunk_count: int