from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import DATABASE_URL
from app.models.entities import Document, KnowledgeChunk, LlmProviderSetting, Question, QuestionProgress, ReviewRecord

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
        missing_chunk_columns = {
            "section_path": "ALTER TABLE knowledgechunk ADD COLUMN section_path VARCHAR",
            "chunk_index": "ALTER TABLE knowledgechunk ADD COLUMN chunk_index INTEGER DEFAULT 0",
            "chunk_type": "ALTER TABLE knowledgechunk ADD COLUMN chunk_type VARCHAR DEFAULT 'paragraph'",
        }
        for column_name, statement in missing_chunk_columns.items():
            if column_name not in chunk_columns:
                connection.execute(text(statement))

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

        provider_columns = {column["name"] for column in inspector.get_columns("llmprovidersetting")} if "llmprovidersetting" in inspector.get_table_names() else set()
        if "llmprovidersetting" in inspector.get_table_names():
            missing_provider_columns = {
                "display_name": "ALTER TABLE llmprovidersetting ADD COLUMN display_name VARCHAR DEFAULT ''",
                "base_url": "ALTER TABLE llmprovidersetting ADD COLUMN base_url VARCHAR",
                "default_model": "ALTER TABLE llmprovidersetting ADD COLUMN default_model VARCHAR",
                "is_enabled": "ALTER TABLE llmprovidersetting ADD COLUMN is_enabled BOOLEAN DEFAULT 1",
                "use_for_chunking": "ALTER TABLE llmprovidersetting ADD COLUMN use_for_chunking BOOLEAN DEFAULT 0",
                "use_for_question_generation": "ALTER TABLE llmprovidersetting ADD COLUMN use_for_question_generation BOOLEAN DEFAULT 0",
                "updated_at": "ALTER TABLE llmprovidersetting ADD COLUMN updated_at TIMESTAMP",
            }
            for column_name, statement in missing_provider_columns.items():
                if column_name not in provider_columns:
                    connection.execute(text(statement))


def get_session():
    """为每次请求提供独立的数据库会话。"""
    with Session(engine) as session:
        yield session