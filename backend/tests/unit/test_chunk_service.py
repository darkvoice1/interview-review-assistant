from app.services.chunk_service import ChunkService


def test_create_chunks_builds_multiple_knowledge_chunks_from_one_section() -> None:
    """知识点服务应能把一个 section 拆成多个更合理的 chunk。"""
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
    assert chunks[0].section_path == "Redis"
    assert chunks[0].chunk_index == 0
    assert chunks[0].chunk_type == "paragraph"
    assert "Redis 是内存数据库" in chunks[0].content
    assert chunks[1].chunk_index == 1
    assert chunks[1].chunk_type == "unordered_list"
    assert "- 读性能高" in chunks[1].content


def test_create_chunks_keeps_code_block_and_image_context() -> None:
    """代码块和图片应进入规则切分链路，而不是被直接丢弃。"""
    service = ChunkService()
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