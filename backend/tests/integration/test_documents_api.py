from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

import app.db.session as session_module
import app.main as main_module
import app.services.document_service as document_service_module
from app.db.session import get_session
from app.main import app


def test_upload_and_list_documents(monkeypatch, tmp_path: Path) -> None:
    """上传接口应能保存 Markdown 并在列表接口中返回。"""
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
                files={"file": ("redis.md", b"# Redis\n\nAOF persistence.", "text/markdown")},
            )
            assert upload_response.status_code == 200
            upload_data = upload_response.json()
            assert upload_data["title"] == "redis"
            assert upload_data["source_type"] == "markdown"
            assert upload_data["file_path"].startswith("storage/documents/")

            list_response = client.get("/api/documents")
            assert list_response.status_code == 200
            list_data = list_response.json()
            assert len(list_data) == 1
            assert list_data[0]["title"] == "redis"
            assert storage_dir.exists()
            assert len(list(storage_dir.glob("*.md"))) == 1
    finally:
        app.dependency_overrides.clear()