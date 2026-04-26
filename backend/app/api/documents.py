from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.document import DocumentRead
from app.services.document_service import DocumentServiceError, document_service

# 文档相关接口。
router = APIRouter()


@router.get("", response_model=list[DocumentRead])
def list_documents(session: Session = Depends(get_session)) -> list[DocumentRead]:
    """返回当前系统中已经上传并入库的文档列表。"""
    # 接口层只负责调用服务层并组织响应结构。
    documents = document_service.list_documents(session)
    return [DocumentRead.model_validate(document) for document in documents]


@router.post("/upload", response_model=DocumentRead)
async def upload_document(
    file: UploadFile,
    session: Session = Depends(get_session),
) -> DocumentRead:
    """接收 Markdown 文件上传，并调用服务层完成保存与落库。"""
    # 读取上传内容后，把业务逻辑交给服务层处理。
    content_bytes = await file.read()
    try:
        document = document_service.create_document_from_upload(
            session=session,
            filename=file.filename,
            content_bytes=content_bytes,
        )
    except DocumentServiceError as exc:
        # 服务层只抛业务异常，接口层负责转成 HTTP 错误。
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return DocumentRead.model_validate(document)