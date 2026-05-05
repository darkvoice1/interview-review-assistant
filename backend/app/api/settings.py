from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.settings import (
    LlmProviderConnectivityTestRead,
    LlmProviderConnectivityTestRequest,
    LlmProviderSettingCreate,
    LlmProviderSettingRead,
    SettingsSummaryRead,
)
from app.services.llm_service import LlmGatewayError, llm_gateway_service
from app.services.settings_service import settings_service

router = APIRouter()


@router.get("", response_model=SettingsSummaryRead)
def get_settings(session: Session = Depends(get_session)) -> SettingsSummaryRead:
    """返回当前大模型设置页所需的全部配置摘要。"""
    summary = settings_service.list_settings(session)
    return SettingsSummaryRead(
        providers=[
            LlmProviderSettingRead(
                id=item.provider.id,
                provider_name=item.provider.provider_name,
                display_name=item.provider.display_name,
                base_url=item.provider.base_url,
                api_key_masked=item.api_key_masked,
                default_model=item.provider.default_model,
                is_enabled=item.provider.is_enabled,
                use_for_chunking=item.provider.use_for_chunking,
                use_for_question_generation=item.provider.use_for_question_generation,
                created_at=item.provider.created_at,
                updated_at=item.provider.updated_at,
            )
            for item in summary.items
        ],
        active_chunking_provider_id=summary.active_chunking_provider_id,
        active_question_generation_provider_id=summary.active_question_generation_provider_id,
    )


@router.post("/providers", response_model=LlmProviderSettingRead)
def save_provider(payload: LlmProviderSettingCreate, session: Session = Depends(get_session)) -> LlmProviderSettingRead:
    """新增或更新单个大模型厂商配置。"""
    provider = settings_service.save_provider(
        session,
        provider_name=payload.provider_name,
        display_name=payload.display_name,
        base_url=payload.base_url,
        api_key=payload.api_key,
        default_model=payload.default_model,
        is_enabled=payload.is_enabled,
        use_for_chunking=payload.use_for_chunking,
        use_for_question_generation=payload.use_for_question_generation,
    )
    return LlmProviderSettingRead(
        id=provider.id,
        provider_name=provider.provider_name,
        display_name=provider.display_name,
        base_url=provider.base_url,
        api_key_masked=settings_service._mask_api_key(provider.api_key),
        default_model=provider.default_model,
        is_enabled=provider.is_enabled,
        use_for_chunking=provider.use_for_chunking,
        use_for_question_generation=provider.use_for_question_generation,
        created_at=provider.created_at,
        updated_at=provider.updated_at,
    )


@router.post("/providers/test", response_model=LlmProviderConnectivityTestRead)
def test_provider_connectivity(payload: LlmProviderConnectivityTestRequest) -> LlmProviderConnectivityTestRead:
    """使用前端当前填写的配置做一次最小连通性测试。"""
    try:
        result = llm_gateway_service.test_provider_connectivity(
            provider_name=payload.provider_name,
            display_name=payload.display_name,
            base_url=payload.base_url,
            api_key=payload.api_key,
            default_model=payload.default_model,
        )
    except LlmGatewayError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return LlmProviderConnectivityTestRead(
        success=result.success,
        provider_name=result.provider_name,
        display_name=result.display_name,
        base_url=result.base_url,
        model=result.model,
        message=result.message,
    )