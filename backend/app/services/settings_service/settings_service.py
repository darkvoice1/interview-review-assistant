from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from sqlmodel import Session, select

from app.core.time_utils import utc_now
from app.models.entities import LlmProviderSetting

SettingsTask = Literal["chunking", "question_generation"]


class SettingsServiceError(ValueError):
    """表示设置业务处理中出现的可预期错误。"""


@dataclass
class SettingsSummaryItem:
    """描述设置页单个厂商配置的内部结构。"""

    provider: LlmProviderSetting
    api_key_masked: str


@dataclass
class SettingsSummaryResult:
    """描述设置页整体摘要结果。"""

    items: list[SettingsSummaryItem]
    active_chunking_provider_id: int | None
    active_question_generation_provider_id: int | None


class SettingsService:
    """封装大模型厂商配置的保存、查询和启用切换逻辑。"""

    task_flag_mapping = {
        "chunking": "use_for_chunking",
        "question_generation": "use_for_question_generation",
    }

    def list_settings(self, session: Session) -> SettingsSummaryResult:
        """返回当前所有大模型厂商配置和启用状态。"""
        statement = select(LlmProviderSetting).order_by(LlmProviderSetting.id.asc())
        providers = session.exec(statement).all()

        items = [
            SettingsSummaryItem(
                provider=provider,
                api_key_masked=self._mask_api_key(provider.api_key),
            )
            for provider in providers
        ]

        active_chunking_provider_id = next(
            (provider.id for provider in providers if provider.use_for_chunking and provider.is_enabled),
            None,
        )
        active_question_generation_provider_id = next(
            (provider.id for provider in providers if provider.use_for_question_generation and provider.is_enabled),
            None,
        )

        return SettingsSummaryResult(
            items=items,
            active_chunking_provider_id=active_chunking_provider_id,
            active_question_generation_provider_id=active_question_generation_provider_id,
        )

    def get_active_provider_for_task(self, session: Session, task: SettingsTask) -> LlmProviderSetting | None:
        """返回某个任务当前启用且可用的厂商配置。"""
        flag_name = self.task_flag_mapping[task]
        statement = (
            select(LlmProviderSetting)
            .where(
                LlmProviderSetting.is_enabled == True,
                getattr(LlmProviderSetting, flag_name) == True,
            )
            .order_by(LlmProviderSetting.updated_at.desc(), LlmProviderSetting.id.desc())
        )
        return session.exec(statement).first()

    def save_provider(
        self,
        session: Session,
        *,
        provider_name: str,
        display_name: str,
        base_url: str | None,
        api_key: str,
        default_model: str | None,
        is_enabled: bool,
        use_for_chunking: bool,
        use_for_question_generation: bool,
    ) -> LlmProviderSetting:
        """新增或按 provider_name 更新一条大模型厂商配置。"""
        statement = select(LlmProviderSetting).where(LlmProviderSetting.provider_name == provider_name)
        provider = session.exec(statement).first()
        now = utc_now()

        if provider is None:
            provider = LlmProviderSetting(
                provider_name=provider_name,
                display_name=display_name,
                base_url=base_url,
                api_key=api_key,
                default_model=default_model,
                is_enabled=is_enabled,
                use_for_chunking=use_for_chunking,
                use_for_question_generation=use_for_question_generation,
                updated_at=now,
            )
            session.add(provider)
        else:
            provider.display_name = display_name
            provider.base_url = base_url
            provider.api_key = api_key
            provider.default_model = default_model
            provider.is_enabled = is_enabled
            provider.use_for_chunking = use_for_chunking
            provider.use_for_question_generation = use_for_question_generation
            provider.updated_at = now

        session.flush()
        self._normalize_active_provider_flags(session, provider)
        session.commit()
        session.refresh(provider)
        return provider

    def _normalize_active_provider_flags(self, session: Session, current_provider: LlmProviderSetting) -> None:
        """保证智能拆分和题目生成各自最多只有一个启用厂商。"""
        providers = session.exec(select(LlmProviderSetting)).all()

        for provider in providers:
            if provider.id == current_provider.id:
                continue

            if current_provider.use_for_chunking and provider.use_for_chunking:
                provider.use_for_chunking = False
            if current_provider.use_for_question_generation and provider.use_for_question_generation:
                provider.use_for_question_generation = False
            provider.updated_at = utc_now()

    def _mask_api_key(self, api_key: str) -> str:
        """对 API Key 做简单脱敏，避免前端直接看到明文。"""
        if len(api_key) <= 8:
            return "*" * len(api_key)
        return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


settings_service = SettingsService()