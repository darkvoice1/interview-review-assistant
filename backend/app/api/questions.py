from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.question import QuestionGenerateResult, QuestionRead, WrongQuestionRead
from app.services.question_service import (
    QuestionDocumentNotFoundError,
    QuestionServiceError,
    question_service,
)

# 题目相关接口。
router = APIRouter()


@router.post("/generate/{document_id}", response_model=QuestionGenerateResult)
def generate_questions(document_id: int, session: Session = Depends(get_session)) -> QuestionGenerateResult:
    """为指定文档生成基础规则题目。"""
    try:
        result = question_service.generate_questions_for_document(session, document_id)
    except QuestionDocumentNotFoundError as exc:
        # 文档不存在时返回 404，方便前端明确提示。
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except QuestionServiceError as exc:
        # 其他可预期业务异常统一返回 400。
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return QuestionGenerateResult(
        document_id=result.document_id,
        chunk_count=result.chunk_count,
        generated_question_count=result.generated_question_count,
        skipped_chunk_count=result.skipped_chunk_count,
    )


@router.get("/wrong", response_model=list[WrongQuestionRead])
def list_wrong_questions(session: Session = Depends(get_session)) -> list[WrongQuestionRead]:
    """返回当前需要重点关注的错题列表。"""
    items = question_service.list_wrong_questions(session)
    return [
        WrongQuestionRead(
            id=item.question.id,
            chunk_id=item.question.chunk_id,
            document_id=item.document_id,
            section_title=item.section_title,
            question_type=item.question.question_type,
            question=item.question.question,
            answer=item.question.answer,
            analysis=item.question.analysis,
            difficulty=item.question.difficulty,
            created_at=item.question.created_at,
            source_title=item.source_title,
            last_feedback=item.last_feedback,
            next_review_at=item.next_review_at,
            review_count=item.review_count,
            mastery_level=item.mastery_level,
        )
        for item in items
    ]


@router.get("", response_model=list[QuestionRead])
def list_questions(
    document_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[QuestionRead]:
    """返回题目列表，支持按文档筛选。"""
    items = question_service.list_questions(session, document_id=document_id)
    return [
        QuestionRead(
            id=item.question.id,
            chunk_id=item.question.chunk_id,
            document_id=item.document_id,
            section_title=item.section_title,
            question_type=item.question.question_type,
            question=item.question.question,
            answer=item.question.answer,
            analysis=item.question.analysis,
            difficulty=item.question.difficulty,
            created_at=item.question.created_at,
        )
        for item in items
    ]
