from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select

import app.db.session as session_module
import app.main as main_module
import app.services.document_service as document_service_module
from app.db.session import get_session
from app.main import app
from app.models.entities import Question, QuestionProgress



def test_generate_and_list_questions_after_upload(monkeypatch, tmp_path: Path) -> None:
    """上传文档后应能保存题目，并初始化题目进度。"""
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
            generate_data = generate_response.json()
            assert generate_data["document_id"] == document_id
            assert generate_data["chunk_count"] == 2
            assert generate_data["generated_question_count"] == 2
            assert generate_data["skipped_chunk_count"] == 0

            list_response = client.get(f"/api/questions?document_id={document_id}")
            assert list_response.status_code == 200
            list_data = list_response.json()
            assert len(list_data) == 2
            assert {item["section_title"] for item in list_data} == {"Redis", "Persistence"}
            assert all(item["document_id"] == document_id for item in list_data)
            assert all(item["question_type"] == "short_answer" for item in list_data)

            regenerate_response = client.post(f"/api/questions/generate/{document_id}")
            assert regenerate_response.status_code == 200
            regenerate_data = regenerate_response.json()
            assert regenerate_data["generated_question_count"] == 0
            assert regenerate_data["skipped_chunk_count"] == 2

        with Session(engine) as session:
            questions = session.exec(select(Question).order_by(Question.id)).all()
            progresses = session.exec(select(QuestionProgress).order_by(QuestionProgress.question_id)).all()
            assert len(questions) == 2
            assert len(progresses) == 2
            assert questions[0].question == "Redis 的核心内容是什么？"
            assert questions[1].question == "Persistence 的核心内容是什么？"
            assert progresses[0].question_id == questions[0].id
            assert progresses[1].question_id == questions[1].id
    finally:
        app.dependency_overrides.clear()



def test_wrong_questions_follow_review_feedback(monkeypatch, tmp_path: Path) -> None:
    """提交不会后题目应进入错题列表，提交会后应从错题列表移出。"""
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

            empty_wrong_response = client.get("/api/questions/wrong")
            assert empty_wrong_response.status_code == 200
            assert empty_wrong_response.json() == []

            submit_wrong_response = client.post(
                "/api/review/submit",
                json={"question_id": question_id, "user_feedback": "不会"},
            )
            assert submit_wrong_response.status_code == 200

            wrong_response = client.get("/api/questions/wrong")
            assert wrong_response.status_code == 200
            wrong_data = wrong_response.json()
            assert len(wrong_data) == 1
            assert wrong_data[0]["id"] == question_id
            assert wrong_data[0]["last_feedback"] == "不会"
            assert wrong_data[0]["review_count"] == 1
            assert wrong_data[0]["mastery_level"] == 0
            assert wrong_data[0]["source_title"] == "Redis"

            submit_right_response = client.post(
                "/api/review/submit",
                json={"question_id": question_id, "user_feedback": "会"},
            )
            assert submit_right_response.status_code == 200

            cleared_wrong_response = client.get("/api/questions/wrong")
            assert cleared_wrong_response.status_code == 200
            assert cleared_wrong_response.json() == []
    finally:
        app.dependency_overrides.clear()
