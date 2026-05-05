from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import DATABASE_URL
from app.models.entities import Document, KnowledgeChunk, Question, QuestionProgress, ReviewRecord

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    """根据当前模型定义创建数据库表，并补齐开发期缺失列。"""
    SQLModel.metadata.create_all(engine)
    _apply_sqlite_dev_migrations()


def _apply_sqlite_dev_migrations() -> None:
    """为当前 SQLite 开发库补齐轻量字段迁移。"""
    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        inspector = inspect(connection)

        chunk_columns = {column["name"] for column in inspector.get_columns("knowledgechunk")}
        if "section_path" not in chunk_columns:
            connection.execute(text("ALTER TABLE knowledgechunk ADD COLUMN section_path VARCHAR"))

        question_columns = {column["name"] for column in inspector.get_columns("question")}
        missing_question_columns = {
            "evidence_kind": "ALTER TABLE question ADD COLUMN evidence_kind VARCHAR",
            "evidence_index": "ALTER TABLE question ADD COLUMN evidence_index INTEGER",
            "evidence_start": "ALTER TABLE question ADD COLUMN evidence_start INTEGER",
            "evidence_end": "ALTER TABLE question ADD COLUMN evidence_end INTEGER",
        }
        for column_name, statement in missing_question_columns.items():
            if column_name not in question_columns:
                connection.execute(text(statement))


def get_session():
    """为每次请求提供独立的数据库会话。"""
    with Session(engine) as session:
        yield session