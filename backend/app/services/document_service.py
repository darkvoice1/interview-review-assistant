from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sqlmodel import Session, select

from app.core.config import BASE_DIR, DOCUMENTS_DIR
from app.models.entities import Document
from app.services.chunk_service import chunk_service
from app.services.markdown_parser import markdown_parser_service


# 文档服务层异常，交给接口层转换为 HTTP 错误。
class DocumentServiceError(ValueError):
    """表示文档业务处理过程中出现的可预期错误。"""

    pass


@dataclass
class DocumentProcessingResult:
    """封装文档上传完成后的文档对象和解析摘要。"""

    document: Document
    chunk_count: int
    section_count: int


# 文档服务，负责处理上传和查询等业务逻辑。
class DocumentService:
    """封装文档上传、保存、解析和查询相关的业务逻辑。"""

    # 第一版只允许上传 Markdown 文件。
    allowed_extensions = {".md", ".markdown"}

    def list_documents(self, session: Session) -> list[Document]:
        """从数据库读取文档列表，并按创建时间倒序返回。"""
        # 从数据库读取已上传文档，按时间倒序返回。
        statement = select(Document).order_by(Document.created_at.desc())
        return session.exec(statement).all()

    def create_document_from_upload(
        self,
        session: Session,
        filename: str | None,
        content_bytes: bytes,
    ) -> DocumentProcessingResult:
        """把上传的 Markdown 文件保存到磁盘、解析结构并生成知识点。"""
        # 先校验文件名和扩展名。
        extension = self._ensure_markdown_file(filename)

        try:
            # 第一版按 UTF-8 读取 Markdown 内容。
            content_raw = content_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentServiceError("Markdown 文件需使用 UTF-8 编码。") from exc

        parsed_result = markdown_parser_service.parse(content_raw)
        document_title = self._resolve_document_title(filename, parsed_result["title"])

        DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

        # 用 uuid 避免同名文件互相覆盖。
        stored_filename = f"{uuid4().hex}{extension}"
        saved_path = DOCUMENTS_DIR / stored_filename
        saved_path.write_text(content_raw, encoding="utf-8")

        document = Document(
            title=document_title,
            source_type="markdown",
            file_path=saved_path.relative_to(BASE_DIR).as_posix(),
            content_raw=content_raw,
        )

        try:
            session.add(document)
            session.flush()

            chunks = chunk_service.create_chunks(document.id, parsed_result["sections"])
            for chunk in chunks:
                session.add(chunk)

            session.commit()
        except Exception:
            session.rollback()
            if saved_path.exists():
                saved_path.unlink()
            raise

        session.refresh(document)
        return DocumentProcessingResult(
            document=document,
            chunk_count=len(chunks),
            section_count=parsed_result["section_count"],
        )

    def _ensure_markdown_file(self, filename: str | None) -> str:
        """校验上传文件名是否存在且属于允许的 Markdown 扩展名。"""
        # 第一版没有文件名时直接判定为非法上传。
        if not filename:
            raise DocumentServiceError("请上传 Markdown 文件。")

        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            raise DocumentServiceError("当前仅支持 .md 或 .markdown 文件。")

        return extension

    def _resolve_document_title(self, filename: str | None, parsed_title: str) -> str:
        """优先使用解析出的标题，解析不到时再退回文件名。"""
        if parsed_title and parsed_title != "Untitled Document":
            return parsed_title
        return Path(filename or "untitled").stem


document_service = DocumentService()