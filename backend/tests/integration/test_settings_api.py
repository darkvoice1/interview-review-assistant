from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

import app.db.session as session_module
from app.db.session import get_session
from app.main import app
from app.services.llm_service import LlmGatewayError, llm_gateway_service
from app.services.settings_service import settings_service



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



def test_save_provider_can_keep_existing_api_key(tmp_path: Path) -> None:
    """更新配置但不重新输入 key 时，应沿用数据库里已保存的 API Key。"""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        provider = settings_service.save_provider(
            session,
            provider_name="openrouter",
            display_name="OpenRouter",
            base_url="https://openrouter.ai/api/v1",
            api_key="sk-or-v1-1234567890abcdef",
            default_model="openai/gpt-4.1-mini",
            is_enabled=True,
            use_for_chunking=False,
            use_for_question_generation=False,
        )
        original_key = provider.api_key

    with Session(engine) as session:
        provider = settings_service.save_provider(
            session,
            provider_name="openrouter",
            display_name="OpenRouter Updated",
            base_url="https://openrouter.ai/api/v1",
            api_key=None,
            default_model="openai/gpt-4.1-mini",
            is_enabled=True,
            use_for_chunking=True,
            use_for_question_generation=False,
        )
        assert provider.display_name == "OpenRouter Updated"
        assert provider.api_key == original_key
        assert provider.use_for_chunking is True



def test_get_active_provider_for_task_returns_enabled_provider(tmp_path: Path) -> None:
    """设置服务应能按任务取回当前启用且可用的厂商。"""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        settings_service.save_provider(
            session,
            provider_name="openrouter",
            display_name="OpenRouter",
            base_url="https://openrouter.ai/api/v1",
            api_key="sk-or-v1-1234567890abcdef",
            default_model="openai/gpt-4.1-mini",
            is_enabled=True,
            use_for_chunking=True,
            use_for_question_generation=False,
        )

    with Session(engine) as session:
        provider = settings_service.get_active_provider_for_task(session, "chunking")
        assert provider is not None
        assert provider.provider_name == "openrouter"
        assert settings_service.get_active_provider_for_task(session, "question_generation") is None



def test_test_provider_connectivity_returns_probe_result(monkeypatch) -> None:
    """设置接口应能返回最小连通性测试结果。"""
    monkeypatch.setattr(
        llm_gateway_service,
        "test_provider_connectivity",
        lambda **kwargs: type(
            "FakeConnectivityResult",
            (),
            {
                "success": True,
                "provider_name": kwargs["provider_name"],
                "display_name": kwargs["display_name"],
                "base_url": kwargs["base_url"],
                "model": kwargs["default_model"],
                "message": "pong",
            },
        )(),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/settings/providers/test",
            json={
                "provider_name": "openrouter",
                "display_name": "OpenRouter",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "sk-or-v1-1234567890abcdef",
                "default_model": "openai/gpt-4.1-mini",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["provider_name"] == "openrouter"
    assert data["model"] == "openai/gpt-4.1-mini"
    assert data["message"] == "pong"



def test_test_provider_connectivity_can_use_saved_api_key(monkeypatch, tmp_path: Path) -> None:
    """测试连接在未重新输入 key 时应能回退到数据库中已保存的 key。"""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    monkeypatch.setattr(session_module, "engine", engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        settings_service.save_provider(
            session,
            provider_name="openrouter",
            display_name="OpenRouter",
            base_url="https://openrouter.ai/api/v1",
            api_key="sk-or-v1-1234567890abcdef",
            default_model="openai/gpt-4.1-mini",
            is_enabled=True,
            use_for_chunking=False,
            use_for_question_generation=False,
        )

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    captured = {}

    def fake_test_provider_connectivity(**kwargs):
        captured.update(kwargs)
        return type(
            "FakeConnectivityResult",
            (),
            {
                "success": True,
                "provider_name": kwargs["provider_name"],
                "display_name": kwargs["display_name"],
                "base_url": kwargs["base_url"],
                "model": kwargs["default_model"],
                "message": "pong",
            },
        )()

    monkeypatch.setattr(llm_gateway_service, "test_provider_connectivity", fake_test_provider_connectivity)

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/settings/providers/test",
                json={
                    "provider_name": "openrouter",
                    "display_name": "OpenRouter",
                    "base_url": "https://openrouter.ai/api/v1",
                    "api_key": None,
                    "default_model": "openai/gpt-4.1-mini",
                    "use_saved_key": True,
                },
            )

        assert response.status_code == 200
        assert captured["api_key"] == "sk-or-v1-1234567890abcdef"
    finally:
        app.dependency_overrides.clear()



def test_test_provider_connectivity_returns_400_when_gateway_rejects(monkeypatch) -> None:
    """设置接口应能把网关层的配置错误转成 400。"""
    monkeypatch.setattr(
        llm_gateway_service,
        "test_provider_connectivity",
        lambda **kwargs: (_ for _ in ()).throw(LlmGatewayError("厂商配置不完整，至少需要可用的 api_key 和 model。")),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/settings/providers/test",
            json={
                "provider_name": "openrouter",
                "display_name": "OpenRouter",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": None,
                "default_model": "",
                "use_saved_key": False,
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "厂商配置不完整，至少需要可用的 api_key 和 model。"