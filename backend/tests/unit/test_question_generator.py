from app.services.llm_service import llm_gateway_service
from app.services.question_service import QuestionGenerationService


def test_generate_drafts_from_chunk_builds_definition_question() -> None:
    """定义型正文应优先生成“什么是”题目。"""
    service = QuestionGenerationService()

    drafts = service.generate_drafts_from_chunk("Redis", "Redis 是一个内存数据库。")

    assert len(drafts) == 1
    assert drafts[0].question_type == "definition_short_answer"
    assert drafts[0].question == "什么是 Redis？"
    assert drafts[0].answer == "Redis 是一个内存数据库。"
    assert drafts[0].evidence_kind == "definition"
    assert drafts[0].evidence_index == 0


def test_generate_drafts_from_chunk_builds_process_question() -> None:
    """流程型正文应优先生成步骤回忆题。"""
    service = QuestionGenerationService()

    drafts = service.generate_drafts_from_chunk(
        "Redis 持久化流程",
        "首先执行 fork，然后子进程写入 RDB 文件，最后替换旧快照。",
    )

    assert len(drafts) == 1
    assert drafts[0].question_type == "process_short_answer"
    assert drafts[0].question == "Redis 持久化流程 的关键步骤是什么？"
    assert "首先执行 fork" in drafts[0].answer
    assert drafts[0].evidence_kind == "process"


def test_generate_drafts_from_chunk_builds_pros_cons_question() -> None:
    """优缺点型正文应优先生成权衡题。"""
    service = QuestionGenerationService()

    drafts = service.generate_drafts_from_chunk(
        "AOF 持久化",
        "AOF 的优点是数据更安全，缺点是文件体积通常更大。",
    )

    assert len(drafts) == 1
    assert drafts[0].question_type == "pros_cons_short_answer"
    assert drafts[0].question == "AOF 持久化 的优点和缺点分别是什么？"
    assert "优点是数据更安全" in drafts[0].answer
    assert drafts[0].evidence_kind == "pros_cons"


def test_generate_drafts_from_chunk_builds_scenario_question() -> None:
    """场景型正文应优先生成场景回忆题。"""
    service = QuestionGenerationService()

    drafts = service.generate_drafts_from_chunk(
        "Redis 缓存",
        "例如在高并发读多写少场景中，Redis 很适合做热点数据缓存。",
    )

    assert len(drafts) == 1
    assert drafts[0].question_type == "scenario_short_answer"
    assert drafts[0].question == "Redis 缓存 更适用于什么场景？"
    assert "高并发读多写少场景" in drafts[0].answer
    assert drafts[0].evidence_kind == "scenario"


def test_generate_drafts_from_chunk_prefers_chunk_type_and_summary_context() -> None:
    """出题时应能利用 chunk_type 和 summary 让题型与问法更贴近知识点。"""
    service = QuestionGenerationService()

    drafts = service.generate_drafts_from_chunk(
        section_title="Redis",
        chunk_text="Redis 常用于缓存场景，尤其适合高频读取与低延迟访问。",
        chunk_type="scenario",
        chunk_summary="缓存适用场景",
        chunk_tags="Redis,缓存",
    )

    assert len(drafts) == 1
    assert drafts[0].question_type == "scenario_short_answer"
    assert drafts[0].question == "Redis（缓存适用场景） 更适用于什么场景？"
    assert "知识点摘要：缓存适用场景" in drafts[0].answer
    assert "关联标签：Redis、缓存" in drafts[0].answer
    assert drafts[0].evidence_kind == "scenario"


def test_generate_drafts_from_chunk_uses_ai_to_rewrite_question_and_answer(monkeypatch) -> None:
    """有可用 session 时，大模型应能同时改写题目和答案表达。"""
    service = QuestionGenerationService()

    def fake_chat_json(session, task, **kwargs):
        assert task == "question_generation"
        return {
            "question": "如果让你解释 Redis 更适合哪些缓存场景，你会怎么回答？",
            "answer": "Redis 常用于高频读取、低延迟访问的缓存场景，尤其适合热点数据访问。",
            "analysis": "检查是否能把适用场景讲清楚。",
            "difficulty": 2,
        }

    monkeypatch.setattr(llm_gateway_service, "chat_json", fake_chat_json)

    drafts = service.generate_drafts_from_chunk(
        section_title="Redis",
        chunk_text="Redis 常用于缓存场景，尤其适合高频读取与低延迟访问。",
        chunk_type="scenario",
        chunk_summary="缓存适用场景",
        chunk_tags="Redis,缓存",
        session=object(),
    )

    assert drafts[0].question == "如果让你解释 Redis 更适合哪些缓存场景，你会怎么回答？"
    assert drafts[0].answer == "Redis 常用于高频读取、低延迟访问的缓存场景，尤其适合热点数据访问。"
    assert drafts[0].difficulty == 2


def test_generate_drafts_from_chunk_returns_empty_for_blank_content() -> None:
    """题目服务遇到空白正文时不应生成无意义题目。"""
    service = QuestionGenerationService()

    drafts = service.generate_drafts_from_chunk("Redis", "   ")

    assert drafts == []


def test_generate_drafts_from_chunk_falls_back_when_no_ai_session() -> None:
    """未传入 session 时应继续走本地规则题目生成。"""
    service = QuestionGenerationService()

    drafts = service.generate_drafts_from_chunk("Redis", "Redis 是一个内存数据库。")

    assert drafts[0].question == "什么是 Redis？"
    assert drafts[0].analysis
