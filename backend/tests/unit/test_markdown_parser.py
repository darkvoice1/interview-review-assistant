from app.services.markdown_parser import MarkdownParserService


def test_parse_extracts_title_preface_and_sections() -> None:
    """解析器应能正确提取标题、前言和 section 内容。"""
    parser = MarkdownParserService()
    content = """Intro line

# Redis
Redis is an in-memory store.

## Persistence
AOF and RDB.

### AOF
Append only file.
"""

    result = parser.parse(content)

    assert result["title"] == "Redis"
    assert result["preface"] == "Intro line"
    assert result["section_count"] == 3
    assert result["sections"][0]["section_title"] == "Redis"
    assert result["sections"][0]["section_level"] == 1
    assert result["sections"][0]["content"] == "Redis is an in-memory store."
    assert result["sections"][1]["section_title"] == "Persistence"
    assert result["sections"][2]["section_title"] == "AOF"