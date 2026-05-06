from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class MarkdownSection:
    """描述单个 Markdown section 的结构化结果。"""

    section_title: str
    section_level: int
    section_path: str
    content: str


@dataclass
class MarkdownParseResult:
    """描述一次 Markdown 解析的完整输出结果。"""

    title: str
    preface: str
    sections: list[MarkdownSection] = field(default_factory=list)
    raw_length: int = 0

    @property
    def section_count(self) -> int:
        """返回当前解析结果中的 section 数量。"""
        return len(self.sections)


class MarkdownParserService:
    """把 Markdown 文本解析成标题层级和 section 正文结构。"""

    heading_pattern = re.compile(r"^(#{1,6})\s+(.*)$")

    def parse(self, content: str) -> MarkdownParseResult:
        """按行扫描 Markdown，提取文档标题、前言和各 section 内容。"""
        lines = content.splitlines()
        sections: list[MarkdownSection] = []
        preface_lines: list[str] = []
        current_section: dict | None = None
        heading_stack: list[tuple[int, str]] = []
        title = "Untitled Document"

        for raw_line in lines:
            line = raw_line.rstrip()
            heading_match = self.heading_pattern.match(line)

            if heading_match:
                if current_section is not None:
                    sections.append(self._build_section(current_section))

                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()

                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, heading_text))
                section_path = " > ".join(title for _, title in heading_stack)

                if level == 1 and title == "Untitled Document":
                    title = heading_text

                current_section = {
                    "section_title": heading_text,
                    "section_level": level,
                    "section_path": section_path,
                    "content_lines": [],
                }
                continue

            if current_section is None:
                preface_lines.append(raw_line)
            else:
                current_section["content_lines"].append(raw_line)

        if current_section is not None:
            sections.append(self._build_section(current_section))

        if title == "Untitled Document" and sections:
            title = sections[0].section_title

        return MarkdownParseResult(
            title=title,
            preface=self._normalize_content(preface_lines),
            sections=sections,
            raw_length=len(content),
        )

    def _build_section(self, section_data: dict) -> MarkdownSection:
        """把解析过程中的临时 section 数据转换成结构化对象。"""
        return MarkdownSection(
            section_title=section_data["section_title"],
            section_level=section_data["section_level"],
            section_path=section_data["section_path"],
            content=self._normalize_content(section_data["content_lines"]),
        )

    def _normalize_content(self, lines: list[str]) -> str:
        """去掉首尾空行，并保留正文原始段落结构。"""
        cleaned_lines = list(lines)
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        return "\n".join(cleaned_lines).strip()


markdown_parser_service = MarkdownParserService()