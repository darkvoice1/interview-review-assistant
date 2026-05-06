from app.services.chunk_service import (
    ChunkEnrichmentService,
    ChunkGenerationService,
    ChunkService,
    ChunkSplitService,
)
from app.services.llm_service import llm_gateway_service


def test_chunk_service_facade_delegates_chunk_creation() -> None:
    """门面应继续提供稳定的 create_chunks 对外入口。"""
    service = ChunkService()
    sections = [
        {
            "section_title": "Redis",
            "section_level": 1,
            "section_path": "Redis",
            "content": "Redis 是内存数据库。\n\n它适合高频读取场景。\n\n- 读性能高\n- 延迟低",
        }
    ]

    chunks = service.create_chunks(document_id=7, sections=sections)

    assert len(chunks) == 2
    assert chunks[0].document_id == 7
    assert chunks[0].section_title == "Redis"
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1


def test_chunk_split_service_keeps_code_block_and_image_context() -> None:
    """代码块和图片应进入规则切分链路，而不是被直接丢弃。"""
    service = ChunkGenerationService()
    sections = [
        {
            "section_title": "AOF",
            "section_level": 2,
            "section_path": "Redis > AOF",
            "content": "AOF 重写示意如下：\n\n```python\nrewrite()\n```\n\n![diagram](aof.png)",
        }
    ]

    chunks = service.create_chunks(document_id=9, sections=sections)

    assert len(chunks) == 1
    assert chunks[0].chunk_type == "paragraph"
    assert "```python" in chunks[0].content
    assert "![diagram](aof.png)" in chunks[0].content


def test_chunk_split_service_detects_invalid_group_order_as_none() -> None:
    """AI 返回非相邻分组时应拒绝采用，避免破坏原始顺序。"""
    split_service = ChunkSplitService()
    enrich_service = ChunkEnrichmentService()
    blocks = split_service.split_section_blocks("第一段。\n\n第二段。\n\n第三段。")

    regrouped = enrich_service.build_blocks_from_groups(blocks, [[0, 2], [1]])

    assert regrouped is None


def test_chunk_generation_service_uses_ai_metadata_to_filter_and_enrich_chunks(monkeypatch) -> None:
    """AI 高层判断应能过滤低价值 chunk，并补充语义类型与元信息。"""
    service = ChunkGenerationService()
    sections = [
        {
            "section_title": "Redis",
            "section_level": 1,
            "section_path": "Redis",
            "content": "Redis 是内存数据库。\n\n它适合高频读取场景。\n\n- 读性能高\n- 延迟低",
        }
    ]

    def fake_chat_json(session, task, **kwargs):
        assert task == "chunking"
        return {
            "chunks": [
                {
                    "index": 0,
                    "keep": True,
                    "chunk_type": "definition",
                    "summary": "Redis 的基础定位",
                    "tags": ["Redis", "缓存"],
                },
                {
                    "index": 1,
                    "keep": False,
                    "chunk_type": "unordered_list",
                    "summary": "",
                    "tags": [],
                },
            ]
        }

    monkeypatch.setattr(llm_gateway_service, "chat_json", fake_chat_json)

    chunks = service.create_chunks(document_id=11, sections=sections, session=object())

    assert len(chunks) == 1
    assert chunks[0].chunk_type == "definition"
    assert chunks[0].summary == "Redis 的基础定位"
    assert chunks[0].tags == "Redis,缓存"
    assert "Redis 是内存数据库" in chunks[0].content


def test_chunk_generation_service_falls_back_when_ai_metadata_is_invalid(monkeypatch) -> None:
    """AI metadata 非法时应回退到本地规则结果。"""
    service = ChunkGenerationService()
    sections = [
        {
            "section_title": "Redis",
            "section_level": 1,
            "section_path": "Redis",
            "content": "Redis 是内存数据库。\n\n它适合高频读取场景。\n\n- 读性能高\n- 延迟低",
        }
    ]

    def fake_chat_json(session, task, **kwargs):
        assert task == "chunking"
        return {"chunks": [{"index": 0, "keep": True}]}

    monkeypatch.setattr(llm_gateway_service, "chat_json", fake_chat_json)

    chunks = service.create_chunks(document_id=12, sections=sections, session=object())

    assert len(chunks) == 2
    assert chunks[0].chunk_type == "paragraph"
    assert chunks[0].summary is None
    assert chunks[0].tags is None
    assert chunks[1].chunk_type == "unordered_list"
