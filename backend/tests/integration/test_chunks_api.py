from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

import app.db.session as session_module
import app.main as main_module
import app.services.document_service as document_service_module
from app.db.session import get_session
from app.main import app



def test_list_and_get_chunks_after_upload(monkeypatch, tmp_path: Path) -> None:
    """上传文档后应能通过 chunks 接口查询细粒度知识点列表和详情。"""
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
            client.post(
                "/api/documents/upload",
                files={
                    "file": (
                        "redis.md",
                        b"# Redis\nRedis intro.\n\n- fast\n- simple\n\n## Persistence\nAOF persistence.",
                        "text/markdown",
                    )
                },
            )

            list_response = client.get("/api/chunks")
            assert list_response.status_code == 200
            chunks = list_response.json()
            assert len(chunks) >= 3
            assert all("chunk_type" in item for item in chunks)
            assert all("chunk_index" in item for item in chunks)
            assert all("section_path" in item for item in chunks)
            assert any(item["chunk_type"] == "unordered_list" for item in chunks)

            chunk_id = chunks[0]["id"]
            detail_response = client.get(f"/api/chunks/{chunk_id}")
            assert detail_response.status_code == 200
            detail = detail_response.json()
            assert detail["id"] == chunk_id
            assert detail["content"]
            assert detail["chunk_type"]
            assert detail["section_path"]

            missing_response = client.get("/api/chunks/99999")
            assert missing_response.status_code == 404
    finally:
        app.dependency_overrides.clear()