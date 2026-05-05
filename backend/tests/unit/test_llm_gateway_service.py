from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine

from app.services.llm_service import llm_gateway_service
from app.services.settings_service import settings_service



def test_llm_gateway_returns_none_without_active_provider(tmp_path: Path) -> None:
    """未配置任务厂商时，网关应直接返回 None。"""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        result = llm_gateway_service.chat_json(
            session,
            "chunking",
            system_prompt="system",
            user_prompt="user",
        )

    assert result is None



def test_llm_gateway_builds_provider_config_from_settings(tmp_path: Path) -> None:
    """网关应能从设置表中读取当前启用厂商配置。"""
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        settings_service.save_provider(
            session,
            provider_name="openrouter",
            display_name="OpenRouter",
            base_url=None,
            api_key="sk-or-v1-1234567890abcdef",
            default_model="openai/gpt-4.1-mini",
            is_enabled=True,
            use_for_chunking=False,
            use_for_question_generation=True,
        )

    with Session(engine) as session:
        provider = llm_gateway_service.get_active_provider_for_task(session, "question_generation")
        assert provider is not None
        assert provider.provider_name == "openrouter"
        assert provider.base_url == "https://openrouter.ai/api/v1"
        assert provider.model == "openai/gpt-4.1-mini"