from __future__ import annotations

from sqlmodel import Session, select

from app.models.entities import Document


class DocumentQueryService:
    """封装文档列表与详情查询相关的业务逻辑。"""

    def list_documents(self, session: Session) -> list[Document]:
        """从数据库读取文档列表，并按创建时间倒序返回。"""
        statement = select(Document).order_by(Document.created_at.desc())
        return session.exec(statement).all()