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
from app.models.entities import QuestionProgress, ReviewRecord



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



def test_submit_review_updates_progress_and_history(monkeypatch, tmp_path: Path) -> None:
    """提交复习反馈后应更新复习记录、进度和今日题单。"""
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
            question_id = today_response.json()["items"][0]["question_id"]

            submit_response = client.post(
                "/api/review/submit",
                json={"question_id": question_id, "user_feedback": "会"},
            )
            assert submit_response.status_code == 200
            submit_data = submit_response.json()
            assert submit_data["question_id"] == question_id
            assert submit_data["user_feedback"] == "会"
            assert submit_data["review_count"] == 1
            assert submit_data["correct_streak"] == 1
            assert submit_data["mastery_level"] == 2

            next_today_response = client.get("/api/review/today")
            assert next_today_response.status_code == 200
            next_today_data = next_today_response.json()
            assert next_today_data["total"] == 1
            assert next_today_data["items"][0]["question_id"] != question_id

        with Session(engine) as session:
            records = session.exec(select(ReviewRecord).order_by(ReviewRecord.id)).all()
            progresses = session.exec(select(QuestionProgress).order_by(QuestionProgress.question_id)).all()
            assert len(records) == 1
            assert records[0].question_id == question_id
            assert records[0].user_feedback == "会"
            assert records[0].quality_score == 2
            assert records[0].next_review_at is not None
            assert records[0].review_time is not None
            assert records[0].next_review_at - records[0].review_time == timedelta(days=5)

            target_progress = next(progress for progress in progresses if progress.question_id == question_id)
            assert target_progress.review_count == 1
            assert target_progress.correct_streak == 1
            assert target_progress.mastery_level == 2
            assert target_progress.last_review_at is not None
            assert target_progress.next_review_at is not None
            assert target_progress.next_review_at - target_progress.last_review_at == timedelta(days=5)
    finally:
        app.dependency_overrides.clear()
