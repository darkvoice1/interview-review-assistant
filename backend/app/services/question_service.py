from dataclasses import dataclass

from sqlmodel import Session, select

from app.models.entities import Document, KnowledgeChunk, Question


class QuestionServiceError(ValueError):
    """表示题目业务处理中出现的可预期错误。"""

    pass


class QuestionDocumentNotFoundError(QuestionServiceError):
    """表示生成题目时目标文档不存在。"""

    pass


@dataclass
class QuestionDraft:
    """描述规则生成器产出的一道待入库题目。"""

    question_type: str
    question: str
    answer: str
    analysis: str | None = None
    difficulty: int = 1


@dataclass
class QuestionGenerationResult:
    """封装一次题目生成完成后的统计结果。"""

    document_id: int
    chunk_count: int
    generated_question_count: int
    skipped_chunk_count: int


@dataclass
class QuestionListItem:
    """描述题目列表项以及它关联的知识点信息。"""

    question: Question
    document_id: int
    section_title: str


# 题目服务，负责题目生成与查询。
class QuestionService:
    """封装题目生成、去重保存和列表查询相关的业务逻辑。"""

    def generate_questions_for_document(self, session: Session, document_id: int) -> QuestionGenerationResult:
        """为指定文档的知识点批量生成基础题目。"""
        document = session.get(Document, document_id)
        if document is None:
            raise QuestionDocumentNotFoundError("目标文档不存在。")

        # 先取出文档下全部知识点，作为规则出题的输入。
        chunk_statement = (
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.id)
        )
        chunks = session.exec(chunk_statement).all()
        if not chunks:
            raise QuestionServiceError("当前文档还没有可生成题目的知识点。")

        chunk_ids = [chunk.id for chunk in chunks if chunk.id is not None]
        existing_chunk_ids = self._load_existing_question_chunk_ids(session, chunk_ids)

        questions_to_create: list[Question] = []
        skipped_chunk_count = 0

        for chunk in chunks:
            # 从数据库取出的知识点理论上都有 id，这里做一次保险判断。
            if chunk.id is None:
                continue

            # 已经生成过题目的知识点先跳过，避免重复入库。
            if chunk.id in existing_chunk_ids:
                skipped_chunk_count += 1
                continue

            drafts = self.generate_drafts_from_chunk(
                section_title=chunk.section_title,
                chunk_text=chunk.content,
            )
            for draft in drafts:
                questions_to_create.append(
                    Question(
                        chunk_id=chunk.id,
                        question_type=draft.question_type,
                        question=draft.question,
                        answer=draft.answer,
                        analysis=draft.analysis,
                        difficulty=draft.difficulty,
                    )
                )

        for question in questions_to_create:
            session.add(question)

        session.commit()
        return QuestionGenerationResult(
            document_id=document_id,
            chunk_count=len(chunks),
            generated_question_count=len(questions_to_create),
            skipped_chunk_count=skipped_chunk_count,
        )

    def generate_drafts_from_chunk(self, section_title: str, chunk_text: str) -> list[QuestionDraft]:
        """基于单个知识点文本生成待入库题目草稿。"""
        # 空内容不生成题目，避免产出无意义题目。
        normalized_text = chunk_text.strip()
        if not normalized_text:
            return []

        # 第一版先按标题生成基础短答题，后续再扩展更多题型。
        return [
            QuestionDraft(
                question_type="short_answer",
                question=f"{section_title} 的核心内容是什么？",
                answer=normalized_text[:120],
                analysis="这道题用于检查你是否能根据标题回忆该知识点的核心内容。",
                difficulty=1,
            )
        ]

    def list_questions(self, session: Session, document_id: int | None = None) -> list[QuestionListItem]:
        """返回题目列表，支持按文档筛选。"""
        statement = (
            select(Question, KnowledgeChunk)
            .join(KnowledgeChunk, KnowledgeChunk.id == Question.chunk_id)
            .order_by(Question.created_at.desc(), Question.id.desc())
        )
        if document_id is not None:
            statement = statement.where(KnowledgeChunk.document_id == document_id)

        rows = session.exec(statement).all()
        return [
            QuestionListItem(
                question=question,
                document_id=chunk.document_id,
                section_title=chunk.section_title,
            )
            for question, chunk in rows
        ]

    def _load_existing_question_chunk_ids(self, session: Session, chunk_ids: list[int]) -> set[int]:
        """读取已经生成过题目的知识点 id，用于避免重复生成。"""
        if not chunk_ids:
            return set()

        statement = select(Question.chunk_id).where(Question.chunk_id.in_(chunk_ids))
        return set(session.exec(statement).all())


question_service = QuestionService()
