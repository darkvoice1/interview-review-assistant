from pathlib import Path
from uuid import uuid4

from sqlmodel import Session, select

from app.core.config import BASE_DIR, DOCUMENTS_DIR
from app.models.entities import Document


# 文档服务层异常，交给接口层转换为 HTTP 错误。
class DocumentServiceError(ValueError):
    pass


# 文档服务，负责处理上传和查询等业务逻辑。
class DocumentService:
    # 第一版只允许上传 Markdown 文件。
    allowed_extensions = {".md", ".markdown"}

    def list_documents(self, session: Session) -> list[Document]:
        # 从数据库读取已上传文档，按时间倒序返回。
        statement = select(Document).order_by(Document.created_at.desc())
        return session.exec(statement).all()

    def create_document_from_upload(
        self,
        session: Session,
        filename: str | None,
        content_bytes: bytes,
    ) -> Document:
        # 先校验文件名和扩展名。
        extension = self._ensure_markdown_file(filename)

        try:
            # 第一版按 UTF-8 读取 Markdown 内容。
            content_raw = content_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentServiceError("Markdown 文件需使用 UTF-8 编码。") from exc

        DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

        # 用 uuid 避免同名文件互相覆盖。
        stored_filename = f"{uuid4().hex}{extension}"
        saved_path = DOCUMENTS_DIR / stored_filename
        saved_path.write_text(content_raw, encoding="utf-8")

        document = Document(
            title=Path(filename or "untitled").stem,
            source_type="markdown",
            file_path=saved_path.relative_to(BASE_DIR).as_posix(),
            content_raw=content_raw,
        )
        session.add(document)
        session.commit()
        session.refresh(document)
        return document

    def _ensure_markdown_file(self, filename: str | None) -> str:
        # 第一版没有文件名时直接判定为非法上传。
        if not filename:
            raise DocumentServiceError("请上传 Markdown 文件。")

        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            raise DocumentServiceError("当前仅支持 .md 或 .markdown 文件。")

        return extension


document_service = DocumentService()