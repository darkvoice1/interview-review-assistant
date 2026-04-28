from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# 题目返回给前端时的结构。
class QuestionRead(BaseModel):
    """描述题目列表返回给前端时的完整字段。"""

    id: int
    chunk_id: int
    document_id: int
    section_title: str
    question_type: str
    question: str
    answer: str
    analysis: Optional[str] = None
    difficulty: int
    created_at: datetime


# 触发题目生成后的结果结构。
class QuestionGenerateResult(BaseModel):
    """描述一次批量生成题目后的统计结果。"""

    document_id: int
    chunk_count: int
    generated_question_count: int
    skipped_chunk_count: int
