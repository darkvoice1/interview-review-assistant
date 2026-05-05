from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.time_utils import utc_now


class Document(SQLModel, table=True):
    """原始导入文档。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    source_type: str = "markdown"
    file_path: Optional[str] = None
    content_raw: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class KnowledgeChunk(SQLModel, table=True):
    """从文档切分出的知识点。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int
    section_title: str
    section_level: int = 1
    section_path: Optional[str] = None
    chunk_index: int = 0
    chunk_type: str = "paragraph"
    content: str
    summary: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)


class Question(SQLModel, table=True):
    """基于知识点生成的题目。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    chunk_id: int
    question_type: str
    question: str
    answer: str
    source_excerpt: Optional[str] = None
    evidence_kind: Optional[str] = None
    evidence_index: Optional[int] = None
    evidence_start: Optional[int] = None
    evidence_end: Optional[int] = None
    analysis: Optional[str] = None
    difficulty: int = 1
    created_at: datetime = Field(default_factory=utc_now)


class ReviewRecord(SQLModel, table=True):
    """每次复习提交后的历史记录。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int
    review_time: datetime = Field(default_factory=utc_now)
    user_feedback: str
    quality_score: Optional[int] = None
    next_review_at: Optional[datetime] = None


class QuestionProgress(SQLModel, table=True):
    """题目的长期掌握状态。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int
    review_count: int = 0
    correct_streak: int = 0
    last_review_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    mastery_level: int = 0