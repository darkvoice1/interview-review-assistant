from __future__ import annotations

from .document_query_service import DocumentQueryService
from .document_upload_service import (
    DocumentProcessingResult,
    DocumentServiceError,
    DocumentUploadService,
)


class DocumentService(DocumentQueryService, DocumentUploadService):
    """文档业务门面，统一组合查询、上传和解析相关能力。"""


document_service = DocumentService()