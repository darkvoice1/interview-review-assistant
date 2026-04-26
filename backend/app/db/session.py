from sqlmodel import Session, SQLModel, create_engine

from app.core.config import DATABASE_URL
from app.models.entities import Document, KnowledgeChunk, Question, QuestionProgress, ReviewRecord

# 创建全局数据库引擎。
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    """根据当前模型定义创建数据库表。"""
    # 启动时创建所有已声明的数据表。
    SQLModel.metadata.create_all(engine)


def get_session():
    """为每次请求提供独立的数据库会话。"""
    # 为每次请求提供独立的数据库会话。
    with Session(engine) as session:
        yield session