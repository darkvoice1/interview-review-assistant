from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LlmProviderSettingCreate(BaseModel):
    """描述新增或更新单个大模型厂商配置时需要的字段。"""

    provider_name: str
    display_name: str
    base_url: Optional[str] = None
    api_key: str = Field(min_length=1)
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