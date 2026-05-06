from __future__ import annotations

from sqlmodel import Session

from app.services.llm_service import llm_gateway_service

from .question_draft_service import QuestionDraft
from .question_evidence_service import QuestionEvidenceUnit


class QuestionAIGenerationService:
    """负责调用大模型润色题目问法和答案表达。"""

    def try_build_ai_draft(
        self,
        *,
        session: Session | None,
        section_title: str,
        chunk_text: str,
        chunk_type: str | None,
        chunk_summary: str | None,
        chunk_tags: str | None,
        evidence: QuestionEvidenceUnit,
        answer_excerpt: str,
        fallback_draft: QuestionDraft,
    ) -> QuestionDraft | None:
        """尝试让大模型改写题目问法和答案表达，失败时回退规则题目。"""
        if session is None:
            return None

        response = llm_gateway_service.chat_json(
            session,
            "question_generation",
            system_prompt=(
                "你是一个面试题润色助手。"
                "你不能引入原文没有出现的新事实，只能基于给定的 section、chunk、summary、tags 和 evidence，"
                "把题目改写得更自然、更像真实面试官发问，同时把答案整理得更适合复习。"
                "请只返回 JSON，对象格式必须为"
                ' {"question": "...", "answer": "...", "analysis": "...", "difficulty": 1}。'
            ),
            user_prompt=(
                f"section_title: {section_title}\n"
                f"chunk_type: {chunk_type or ''}\n"
                f"chunk_summary: {chunk_summary or ''}\n"
                f"chunk_tags: {chunk_tags or ''}\n"
                f"chunk_text: {chunk_text}\n"
                f"evidence_kind: {evidence.kind}\n"
                f"evidence_text: {evidence.text}\n"
                f"必须忠于原文的标准答案: {answer_excerpt}\n"
                f"当前规则题目: {fallback_draft.question}\n"
                f"当前规则答案: {fallback_draft.answer}\n"
                "请输出一个更自然的题目问法和更适合复习的答案表达。"
                "答案可以整理表达顺序，但不能引入原文没有的新事实。difficulty 取 1~3。"
            ),
            temperature=0.4,
        )
        if response is None:
            return None

        question = (response.get("question") or "").strip()
        answer = (response.get("answer") or "").strip()
        analysis = (response.get("analysis") or fallback_draft.analysis or "").strip()
        difficulty = response.get("difficulty", fallback_draft.difficulty)
        if not question:
            return None
        if not answer:
            answer = fallback_draft.answer
        if not isinstance(difficulty, int) or difficulty < 1 or difficulty > 3:
            difficulty = fallback_draft.difficulty

        return QuestionDraft(
            question_type=fallback_draft.question_type,
            question=question,
            answer=answer,
            source_excerpt=answer_excerpt,
            evidence_kind=evidence.kind,
            evidence_index=evidence.index,
            evidence_start=evidence.start,
            evidence_end=evidence.end,
            analysis=analysis or fallback_draft.analysis,
            difficulty=difficulty,
        )


question_ai_generation_service = QuestionAIGenerationService()
