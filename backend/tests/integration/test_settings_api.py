from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

import app.db.session as session_module
from app.db.session import get_session
from app.main import app



def test_save_and_list_llm_provider_settings(monkeypatch, tmp_path: Path) -> None:
    """设置接口应能保存厂商配置、脱敏返回并维护单一启用项。"""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    monkeypatch.setattr(session_module, "engine", engine)
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    try:
        with TestClient(app) as client:
            save_response = client.post(
                "/api/settings/providers",
                json={
                    "provider_name": "openrouter",
                    "display_name": "OpenRouter",
                    "base_url": "https://openrouter.ai/api/v1",
                    "api_key": "sk-or-v1-1234567890abcdef",
                    "default_model": "openai/gpt-4.1-mini",
                    "is_enabled": True,
                    "use_for_chunking": True,
                    "use_for_question_generation": False,
                },
            )
            assert save_response.status_code == 200
            saved_data = save_response.json()
            assert saved_data["provider_name"] == "openrouter"
            assert saved_data["api_key_masked"].startswith("sk-o")
            assert saved_data["use_for_chunking"] is True

            second_response = client.post(
                "/api/settings/providers",
                json={
                    "provider_name": "qwen",
                    "display_name": "Qwen",
                    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                    "api_key": "sk-qwen-abcdefghijklmnopqrstuvwxyz",
                    "default_model": "qwen-max",
                    "is_enabled": True,
                    "use_for_chunking": True,
                    "use_for_question_generation": True,
                },
            )
            assert second_response.status_code == 200

            list_response = client.get("/api/settings")
            assert list_response.status_code == 200
            list_data = list_response.json()
            assert len(list_data["providers"]) == 2
            assert list_data["active_chunking_provider_id"] == second_response.json()["id"]
            assert list_data["active_question_generation_provider_id"] == second_response.json()["id"]

            providers = {item["provider_name"]: item for item in list_data["providers"]}
            assert providers["openrouter"]["use_for_chunking"] is False
            assert providers["qwen"]["use_for_chunking"] is True
            assert providers["qwen"]["use_for_question_generation"] is True
    finally:
        app.dependency_overrides.clear()