from dataclasses import dataclass
from datetime import datetime

from sqlmodel import Session, select

from app.models.entities import Document, KnowledgeChunk, Question, QuestionProgress, ReviewRecord


class QuestionServiceError(ValueError):
    """表示题目业务处理中出现的可预期错误。"""

    pass


class QuestionDocumentNotFoundError(QuestionServiceError):
    """表示生成题目时目标文档不存在。"""

    pass


class QuestionNotFoundError(QuestionServiceError):
    """表示查询题目详情时目标题目不存在。"""

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


@dataclass
class QuestionDetailItem:
    """描述题目详情以及它关联的上下文和复习状态。"""

    question: Question
    document_id: int
    section_title: str
    source_title: str
    source_type: str
    chunk_content: str
    review_count: int
    correct_streak: int
    mastery_level: int
    last_review_at: datetime | None
    next_review_at: datetime | None
    last_feedback: str | None


@dataclass
class WrongQuestionListItem:
    """描述错题列表项以及它关联的复习状态信息。"""

    question: Question
    document_id: int
    section_title: str
    source_title: str
    last_feedback: str | None
    next_review_at: datetime | None
    review_count: int
    mastery_level: int


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

        # 先保存题目，再为每道题初始化复习进度记录。
        for question in questions_to_create:
            session.add(question)

        session.flush()

        for question in questions_to_create:
            if question.id is None:
                continue
            session.add(QuestionProgress(question_id=question.id))

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

    def get_question(self, session: Session, question_id: int) -> QuestionDetailItem:
        """按 id 返回单个题目的详情信息。"""
        statement = (
            select(Question, KnowledgeChunk, Document, QuestionProgress)
            .join(KnowledgeChunk, KnowledgeChunk.id == Question.chunk_id)
            .join(Document, Document.id == KnowledgeChunk.document_id)
            .join(QuestionProgress, QuestionProgress.question_id == Question.id)
            .where(Question.id == question_id)
        )
        row = session.exec(statement).first()
        if row is None:
            raise QuestionNotFoundError("题目不存在。")

        question, chunk, document, progress = row
        return QuestionDetailItem(
            question=question,
            document_id=chunk.document_id,
            section_title=chunk.section_title,
            source_title=document.title,
            source_type=document.source_type,
            chunk_content=chunk.content,
            review_count=progress.review_count,
            correct_streak=progress.correct_streak,
            mastery_level=progress.mastery_level,
            last_review_at=progress.last_review_at,
            next_review_at=progress.next_review_at,
            last_feedback=self._load_latest_feedback(session, question.id),
        )

    def list_wrong_questions(self, session: Session) -> list[WrongQuestionListItem]:
        """返回当前需要重点关注的错题列表。"""
        statement = (
            select(Question, KnowledgeChunk, Document, QuestionProgress)
            .join(KnowledgeChunk, KnowledgeChunk.id == Question.chunk_id)
            .join(Document, Document.id == KnowledgeChunk.document_id)
            .join(QuestionProgress, QuestionProgress.question_id == Question.id)
            .where(QuestionProgress.review_count > 0)
            .where(QuestionProgress.mastery_level < 2)
            .order_by(QuestionProgress.next_review_at.asc(), Question.id.asc())
        )
        rows = session.exec(statement).all()

        items: list[WrongQuestionListItem] = []
        for question, chunk, document, progress in rows:
            items.append(
                WrongQuestionListItem(
                    question=question,
                    document_id=chunk.document_id,
                    section_title=chunk.section_title,
                    source_title=document.title,
                    last_feedback=self._load_latest_feedback(session, question.id),
                    next_review_at=progress.next_review_at,
                    review_count=progress.review_count,
                    mastery_level=progress.mastery_level,
                )
            )

        return items

    def _load_existing_question_chunk_ids(self, session: Session, chunk_ids: list[int]) -> set[int]:
        """读取已经生成过题目的知识点 id，用于避免重复生成。"""
        if not chunk_ids:
            return set()

        statement = select(Question.chunk_id).where(Question.chunk_id.in_(chunk_ids))
        return set(session.exec(statement).all())

    def _load_latest_feedback(self, session: Session, question_id: int | None) -> str | None:
        """读取某道题最近一次复习反馈。"""
        if question_id is None:
            return None

        statement = (
            select(ReviewRecord.user_feedback)
            .where(ReviewRecord.question_id == question_id)
            .order_by(ReviewRecord.review_time.desc(), ReviewRecord.id.desc())
        )
        return session.exec(statement).first()


question_service = QuestionService()
