from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# 文档创建时的请求体。
class DocumentCreate(BaseModel):
    """描述新建文档时需要返回或传递的基础字段。"""

    title: str
    source_type: str = "markdown"


# 文档返回给前端时的结构。
class DocumentRead(DocumentCreate):
    """描述文档详情或列表项返回给前端时的完整结构。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: Optional[str] = None
    created_at: datetime


# 文档上传完成后的结果结构。
class DocumentUploadResult(DocumentRead):
    """描述上传完成后返回的文档和解析摘要。"""

    chunk_count: int
    section_count: int