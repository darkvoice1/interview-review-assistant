from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# 文档创建时的请求体。
class DocumentCreate(BaseModel):
    title: str
    source_type: str = "markdown"


# 文档返回给前端时的结构。
class DocumentRead(DocumentCreate):
    id: int
    file_path: Optional[str] = None
    created_at: datetime
