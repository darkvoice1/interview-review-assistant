from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select

import app.db.session as session_module
import app.main as main_module
import app.services.document_service as document_service_module
from app.db.session import get_session
from app.main import app
from app.models.entities import KnowledgeChunk, Question
from app.services.llm_service import llm_gateway_service



def test_upload_and_generate_use_ai_enhancement_when_provider_is_enabled(monkeypatch, tmp_path: Path) -> None:
    """启用厂商后，chunk regroup 和题目问法应能进入 AI 增强分支。"""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    storage_dir = tmp_path / "storage" / "documents"

    monkeypatch.setattr(session_module, "engine", engine)
    monkeypatch.setattr(main_module, "DOCUMENTS_DIR", storage_dir)
    monkeypatch.setattr(document_service_module, "BASE_DIR", tmp_path)
    monkeypatch.setattr(document_service_module, "DOCUMENTS_DIR", storage_dir)

    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    call_log: list[str] = []

    def fake_chat_json(session, task, **kwargs):
        call_log.append(task)
        if task == "chunking":
            return {"groups": [[0, 1], [2]]}
        if task == "question_generation":
            return {
                "question": "面试中你会如何解释 Redis 为什么适合做高频读取缓存？",
                "analysis": "检查是否能结合原文说明 Redis 的核心适用性。",
                "difficulty": 2,
            }
        return None

    monkeypatch.setattr(llm_gateway_service, "chat_json", fake_chat_json)

    try:
        with TestClient(app) as client:
            provider_response = client.post(
                "/api/settings/providers",
                json={
                    "provider_name": "openrouter",
                    "display_name": "OpenRouter",
                    "base_url": "https://openrouter.ai/api/v1",
                    "api_key": "sk-or-v1-1234567890abcdef",
                    "default_model": "openai/gpt-4.1-mini",
                    "is_enabled": True,
                    "use_for_chunking": True,
                    "use_for_question_generation": True,
                },
            )
            assert provider_response.status_code == 200

            upload_response = client.post(
                "/api/documents/upload",
                files={
                    "file": (
                        "redis.md",
                        (
                            "# Redis\n"
                            "Redis 是一个高性能内存数据库，支持丰富数据结构，并且经常作为缓存层来承接高并发请求。\n\n"
                            "它特别适合高频读取、低延迟响应且需要热点数据快速访问的业务场景，这也是面试中经常被提到的原因。\n\n"
                            "- 读性能高\n- 延迟低"
                        ).encode("utf-8"),
                        "text/markdown",
                    )
                },
            )
            assert upload_response.status_code == 200
            document_id = upload_response.json()["id"]
            assert upload_response.json()["chunk_count"] == 2

            generate_response = client.post(f"/api/questions/generate/{document_id}")
            assert generate_response.status_code == 200
            assert generate_response.json()["generated_question_count"] == 2

        with Session(engine) as session:
            chunks = session.exec(select(KnowledgeChunk).order_by(KnowledgeChunk.chunk_index)).all()
            questions = session.exec(select(Question).order_by(Question.id)).all()
            assert len(chunks) == 2
            assert "Redis 是一个高性能内存数据库" in chunks[0].content
            assert "它特别适合高频读取" in chunks[0].content
            assert questions[0].question == "面试中你会如何解释 Redis 为什么适合做高频读取缓存？"
            assert questions[0].difficulty == 2

        assert "chunking" in call_log
        assert "question_generation" in call_log
    finally:
        app.dependency_overrides.clear()