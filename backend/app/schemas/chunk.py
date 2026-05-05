from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ChunkRead(BaseModel):
    """描述知识点列表项或详情返回给前端时的结构。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    section_title: str
    section_level: int
    section_path: Optional[str] = None
    chunk_index: int
    chunk_type: str
    content: str
    summary: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime