from app.services.question_service import QuestionService


def test_generate_drafts_from_chunk_builds_definition_question() -> None:
    """定义型正文应优先生成“什么是”题目。"""
    service = QuestionService()

    drafts = service.generate_drafts_from_chunk("Redis", "Redis 是一个内存数据库。")

    assert len(drafts) == 1
    assert drafts[0].question_type == "definition_short_answer"
    assert drafts[0].question == "什么是 Redis？"
    assert drafts[0].answer == "Redis 是一个内存数据库。"
    assert drafts[0].evidence_kind == "definition"
    assert drafts[0].evidence_index == 0


def test_generate_drafts_from_chunk_builds_process_question() -> None:
    """流程型正文应优先生成步骤回忆题。"""
    service = QuestionService()

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
    service = QuestionService()

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
    service = QuestionService()

    drafts = service.generate_drafts_from_chunk(
        "Redis 缓存",
        "例如在高并发读多写少场景中，Redis 很适合做热点数据缓存。",
    )

    assert len(drafts) == 1
    assert drafts[0].question_type == "scenario_short_answer"
    assert drafts[0].question == "Redis 缓存 更适用于什么场景？"
    assert "高并发读多写少场景" in drafts[0].answer
    assert drafts[0].evidence_kind == "scenario"


def test_generate_drafts_from_chunk_returns_empty_for_blank_content() -> None:
    """题目服务遇到空白正文时不应生成无意义题目。"""
    service = QuestionService()

    drafts = service.generate_drafts_from_chunk("Redis", "   ")

    assert drafts == []


def test_generate_drafts_from_chunk_falls_back_when_no_ai_session() -> None:
    """未传入 session 时应继续走本地规则题目生成。"""
    service = QuestionService()

    drafts = service.generate_drafts_from_chunk("Redis", "Redis 是一个内存数据库。")

    assert drafts[0].question == "什么是 Redis？"
    assert drafts[0].analysis