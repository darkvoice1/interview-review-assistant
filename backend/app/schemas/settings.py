from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LlmProviderSettingCreate(BaseModel):
    """描述新增或更新单个大模型厂商配置时需要的字段。"""

    provider_name: str
    display_name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    is_enabled: bool = True
    use_for_chunking: bool = False
    use_for_question_generation: bool = False


class LlmProviderSettingRead(BaseModel):
    """描述返回给前端的单个大模型厂商配置。"""

    id: int
    provider_name: str
    display_name: str
    base_url: Optional[str] = None
    api_key_masked: str
    default_model: Optional[str] = None
    is_enabled: bool
    use_for_chunking: bool
    use_for_question_generation: bool
    created_at: datetime
    updated_at: datetime


class SettingsSummaryRead(BaseModel):
    """描述设置页的整体返回结构。"""

    providers: list[LlmProviderSettingRead]
    active_chunking_provider_id: Optional[int] = None
    active_question_generation_provider_id: Optional[int] = None


class LlmProviderConnectivityTestRequest(BaseModel):
    """描述前端发起厂商连通性测试时提交的配置。"""

    provider_name: str
    display_name: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    use_saved_key: bool = False


class LlmProviderConnectivityTestRead(BaseModel):
    """描述厂商连通性测试的返回结果。"""

    success: bool
    provider_name: str
    display_name: str
    base_url: str
    model: str
    message: str