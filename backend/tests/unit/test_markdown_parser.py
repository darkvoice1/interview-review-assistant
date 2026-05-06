from app.services.document_service import MarkdownParseResult, MarkdownParserService, MarkdownSection


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

    assert isinstance(result, MarkdownParseResult)
    assert result.title == "Redis"
    assert result.preface == "Intro line"
    assert result.section_count == 3
    assert isinstance(result.sections[0], MarkdownSection)

    top_section = result.sections[0]
    assert top_section.section_index == 0
    assert top_section.section_title == "Redis"
    assert top_section.section_level == 1
    assert top_section.section_path == "Redis"
    assert top_section.parent_section_title is None
    assert top_section.parent_section_path is None
    assert top_section.heading_line_number == 3
    assert top_section.content_start_line_number == 4
    assert top_section.content_end_line_number == 4
    assert top_section.content == "Redis is an in-memory store."

    middle_section = result.sections[1]
    assert middle_section.section_index == 1
    assert middle_section.section_title == "Persistence"
    assert middle_section.section_path == "Redis > Persistence"
    assert middle_section.parent_section_title == "Redis"
    assert middle_section.parent_section_path == "Redis"
    assert middle_section.heading_line_number == 6
    assert middle_section.content_start_line_number == 7
    assert middle_section.content_end_line_number == 7

    leaf_section = result.sections[2]
    assert leaf_section.section_index == 2
    assert leaf_section.section_title == "AOF"
    assert leaf_section.section_path == "Redis > Persistence > AOF"
    assert leaf_section.parent_section_title == "Persistence"
    assert leaf_section.parent_section_path == "Redis > Persistence"
    assert leaf_section.heading_line_number == 9
    assert leaf_section.content_start_line_number == 10
    assert leaf_section.content_end_line_number == 10


def test_parse_preserves_section_position_when_content_has_blank_lines() -> None:
    """解析器应能识别正文首尾空行之外的真实内容行号。"""
    parser = MarkdownParserService()
    content = """# Topic

Line 1

Line 2

## Child

Child line
"""

    result = parser.parse(content)

    parent_section = result.sections[0]
    assert parent_section.content == "Line 1\n\nLine 2"
    assert parent_section.content_start_line_number == 3
    assert parent_section.content_end_line_number == 5

    child_section = result.sections[1]
    assert child_section.content == "Child line"
    assert child_section.content_start_line_number == 9
    assert child_section.content_end_line_number == 9
