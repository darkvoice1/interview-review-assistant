import re


# Markdown 解析服务，负责抽取标题层级和正文内容。
class MarkdownParserService:
    """把 Markdown 文本解析成标题层级和 section 正文结构。"""

    heading_pattern = re.compile(r"^(#{1,6})\s+(.*)$")

    def parse(self, content: str) -> dict:
        """按行扫描 Markdown，提取文档标题、前言和各 section 内容。"""
        # 先按行扫描 Markdown，提取标题和对应正文。
        lines = content.splitlines()
        sections: list[dict] = []
        preface_lines: list[str] = []
        current_section: dict | None = None
        title = "Untitled Document"

        for raw_line in lines:
            line = raw_line.rstrip()
            heading_match = self.heading_pattern.match(line)

            if heading_match:
                # 遇到新标题时，先收束上一个 section。
                if current_section is not None:
                    current_section["content"] = self._normalize_content(current_section["content_lines"])
                    current_section.pop("content_lines")
                    sections.append(current_section)

                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()

                # 第一条一级标题优先作为文档标题。
                if level == 1 and title == "Untitled Document":
                    title = heading_text

                current_section = {
                    "section_title": heading_text,
                    "section_level": level,
                    "content_lines": [],
                }
                continue

            # 标题出现前的内容暂存为前言。
            if current_section is None:
                preface_lines.append(raw_line)
            else:
                current_section["content_lines"].append(raw_line)

        # 处理最后一个 section。
        if current_section is not None:
            current_section["content"] = self._normalize_content(current_section["content_lines"])
            current_section.pop("content_lines")
            sections.append(current_section)

        # 如果没有一级标题，就尝试用第一个 section 作为文档标题。
        if title == "Untitled Document" and sections:
            title = sections[0]["section_title"]

        return {
            "title": title,
            "preface": self._normalize_content(preface_lines),
            "sections": sections,
            "raw_length": len(content),
            "section_count": len(sections),
        }

    def _normalize_content(self, lines: list[str]) -> str:
        """去掉首尾空行，并保留正文原始段落结构。"""
        # 去掉首尾空行，保留正文原始段落结构。
        cleaned_lines = list(lines)
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        return "\n".join(cleaned_lines).strip()