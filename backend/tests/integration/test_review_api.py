from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select

import app.db.session as session_module
import app.main as main_module
import app.services.document_service as document_service_module
from app.core.time_utils import utc_now
from app.db.session import get_session
from app.main import app
from app.models.entities import QuestionProgress



def test_today_review_returns_new_and_due_questions(monkeypatch, tmp_path: Path) -> None:
    """今日题单接口应能返回新题，并过滤掉未到期题目。"""
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

    try:
        with TestClient(app) as client:
            upload_response = client.post(
                "/api/documents/upload",
                files={
                    "file": (
                        "redis.md",
                        b"# Redis\nRedis intro.\n\n## Persistence\nAOF persistence.",
                        "text/markdown",
                    )
                },
            )
            assert upload_response.status_code == 200
            document_id = upload_response.json()["id"]

            generate_response = client.post(f"/api/questions/generate/{document_id}")
            assert generate_response.status_code == 200

            today_response = client.get("/api/review/today")
            assert today_response.status_code == 200
            today_data = today_response.json()
            assert today_data["total"] == 2
            assert {item["source_title"] for item in today_data["items"]} == {"Redis"}

        with Session(engine) as session:
            progresses = session.exec(select(QuestionProgress).order_by(QuestionProgress.question_id)).all()
            assert len(progresses) == 2
            progresses[0].next_review_at = utc_now() - timedelta(days=1)
            progresses[1].next_review_at = utc_now() + timedelta(days=1)
            session.commit()

        with TestClient(app) as client:
            due_response = client.get("/api/review/today")
            assert due_response.status_code == 200
            due_data = due_response.json()
            assert due_data["total"] == 1
            assert due_data["items"][0]["question"] in {
                "Redis 的核心内容是什么？",
                "Persistence 的核心内容是什么？",
            }
            assert due_data["items"][0]["source_title"] == "Redis"
    finally:
        app.dependency_overrides.clear()
