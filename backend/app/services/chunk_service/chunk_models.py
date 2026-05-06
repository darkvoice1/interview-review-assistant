from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SectionBlock:
    """描述 section 内部拆出的中间块结构。"""

    block_type: str
    content: str
    summary: str | None = None
    tags: list[str] | None = None
