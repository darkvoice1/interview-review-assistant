from app.services.question_service import QuestionService



def test_generate_drafts_from_chunk_builds_basic_short_answer() -> None:
    """题目服务应能根据知识点标题和正文生成基础短答题。"""
    service = QuestionService()

    drafts = service.generate_drafts_from_chunk("Redis", "Redis 是一个内存数据库。")

    assert len(drafts) == 1
    assert drafts[0].question_type == "short_answer"
    assert drafts[0].question == "Redis 的核心内容是什么？"
    assert drafts[0].answer == "Redis 是一个内存数据库。"



def test_generate_drafts_from_chunk_returns_empty_for_blank_content() -> None:
    """题目服务遇到空白正文时不应生成无意义题目。"""
    service = QuestionService()

    drafts = service.generate_drafts_from_chunk("Redis", "   ")

    assert drafts == []
