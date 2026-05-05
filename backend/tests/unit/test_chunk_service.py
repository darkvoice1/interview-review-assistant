from app.services.chunk_service import ChunkService


def test_create_chunks_builds_knowledge_chunk_models() -> None:
    """知识点服务应能把 section 结果转换成知识点实体。"""
    service = ChunkService()
    sections = [
        {"section_title": "Redis", "section_level": 1, "section_path": "Redis", "content": "Redis body"},
        {
            "section_title": "Persistence",
            "section_level": 2,
            "section_path": "Redis > Persistence",
            "content": "AOF and RDB",
        },
    ]

    chunks = service.create_chunks(document_id=7, sections=sections)

    assert len(chunks) == 2
    assert chunks[0].document_id == 7
    assert chunks[0].section_title == "Redis"
    assert chunks[0].section_path == "Redis"
    assert chunks[1].section_level == 2
    assert chunks[1].section_path == "Redis > Persistence"
    assert chunks[1].content == "AOF and RDB"