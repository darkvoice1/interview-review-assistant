from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class MarkdownSection:
    """描述单个 Markdown section 的结构化结果。"""

    section_index: int
    section_title: str
    section_level: int
    section_path: str
    parent_section_title: str | None
    parent_section_path: str | None
    heading_line_number: int
    content_start_line_number: int | None
    content_end_line_number: int | None
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

        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.rstrip()
            heading_match = self.heading_pattern.match(line)

            if heading_match:
                if current_section is not None:
                    sections.append(self._build_section(current_section))

                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()

                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()

                parent_section_title = heading_stack[-1][1] if heading_stack else None
                parent_section_path = " > ".join(title for _, title in heading_stack) if heading_stack else None

                heading_stack.append((level, heading_text))
                section_path = " > ".join(title for _, title in heading_stack)

                if level == 1 and title == "Untitled Document":
                    title = heading_text

                current_section = {
                    "section_index": len(sections),
                    "section_title": heading_text,
                    "section_level": level,
                    "section_path": section_path,
                    "parent_section_title": parent_section_title,
                    "parent_section_path": parent_section_path,
                    "heading_line_number": line_number,
                    "content_lines": [],
                    "content_line_numbers": [],
                }
                continue

            if current_section is None:
                preface_lines.append(raw_line)
            else:
                current_section["content_lines"].append(raw_line)
                current_section["content_line_numbers"].append(line_number)

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
        content_start_line_number = self._resolve_content_start_line_number(
            section_data["content_lines"],
            section_data["content_line_numbers"],
        )
        content_end_line_number = self._resolve_content_end_line_number(
            section_data["content_lines"],
            section_data["content_line_numbers"],
        )
        return MarkdownSection(
            section_index=section_data["section_index"],
            section_title=section_data["section_title"],
            section_level=section_data["section_level"],
            section_path=section_data["section_path"],
            parent_section_title=section_data["parent_section_title"],
            parent_section_path=section_data["parent_section_path"],
            heading_line_number=section_data["heading_line_number"],
            content_start_line_number=content_start_line_number,
            content_end_line_number=content_end_line_number,
            content=self._normalize_content(section_data["content_lines"]),
        )

    def _resolve_content_start_line_number(
        self,
        lines: list[str],
        line_numbers: list[int],
    ) -> int | None:
        """返回当前 section 第一行非空正文在原文中的行号。"""
        for line, line_number in zip(lines, line_numbers):
            if line.strip():
                return line_number
        return None

    def _resolve_content_end_line_number(
        self,
        lines: list[str],
        line_numbers: list[int],
    ) -> int | None:
        """返回当前 section 最后一行非空正文在原文中的行号。"""
        for line, line_number in zip(reversed(lines), reversed(line_numbers)):
            if line.strip():
                return line_number
        return None

    def _normalize_content(self, lines: list[str]) -> str:
        """去掉首尾空行，并保留正文原始段落结构。"""
        cleaned_lines = list(lines)
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        return "\n".join(cleaned_lines).strip()


markdown_parser_service = MarkdownParserService()
