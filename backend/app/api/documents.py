from datetime import datetime

from fastapi import APIRouter, UploadFile

from app.schemas.document import DocumentCreate, DocumentRead

# 文档相关接口。
router = APIRouter()

@router.get("", response_model=list[DocumentRead])
def list_documents() -> list[DocumentRead]:
    # 这里先返回占位数据，后续替换为数据库查询。
    return [
        DocumentRead(
            id=1,
            title="Redis Interview Notes",
            source_type="markdown",
            file_path="notes/redis.md",
            created_at=datetime.utcnow(),
        )
    ]


@router.post("/upload", response_model=DocumentCreate)
async def upload_document(file: UploadFile) -> DocumentCreate:
    # 先保留上传入口，后续补真实保存和解析流程。
    return DocumentCreate(title=file.filename or "untitled", source_type="markdown")
