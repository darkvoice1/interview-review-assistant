from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


# 原始导入文档。
class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    source_type: str = "markdown"
    file_path: Optional[str] = None
    content_raw: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# 从文档切分出的知识点。
class KnowledgeChunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int
    section_title: str
    section_level: int = 1
    content: str
    summary: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# 基于知识点生成的题目。
class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chunk_id: int
    question_type: str
    question: str
    answer: str
    analysis: Optional[str] = None
    difficulty: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)


# 每次复习提交后的历史记录。
class ReviewRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int
    review_time: datetime = Field(default_factory=datetime.utcnow)
    user_feedback: str
    quality_score: Optional[int] = None
    next_review_at: Optional[datetime] = None


# 题目的长期掌握状态。
class QuestionProgress(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question_id: int
    review_count: int = 0
    correct_streak: int = 0
    last_review_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    mastery_level: int = 0
