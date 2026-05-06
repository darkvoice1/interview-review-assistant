from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class QuestionEvidenceUnit:
    """描述一条从原文中提取出来的结构化证据单元。"""

    kind: str
    text: str
    index: int
    start: int
    end: int


class QuestionEvidenceService:
    """负责把 chunk 正文拆成证据单元，并判断更适合的题型。"""

    split_pattern = re.compile(r"(?<=[\u3002\uff01\uff1f\uff1b;])\s*|\n+")
    bullet_prefix_pattern = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)?]\s*)")

    comparison_keywords = ('区别', '不同', '相比', '对比', '异同', '相同')
    pros_cons_keywords = ('优缺点', '优点', '缺点', '优势', '劣势')
    process_keywords = ('步骤', '流程', '过程', '首先', '然后', '最后', '第一', '第二', '第三')
    reason_keywords = ('原因', '为什么', '因为', '目的', '作用', '意义')
    scenario_keywords = ('比如', '例如', '场景', '适用于', '适合', '实践中', '面试中')
    definition_pattern = re.compile(r"^[^\u3002\uff01\uff1f\uff1b;]{0,24}(?:\u662f|\u6307|\u8868\u793a|\u7528\u4e8e|\u7528\u6765|\u8d1f\u8d23)")

    def extract_evidence_units(self, chunk_text: str) -> list[QuestionEvidenceUnit]:
        """把正文提取成可出题的结构化原文证据单元。"""
        units: list[QuestionEvidenceUnit] = []
        search_start = 0

        for index, raw_unit in enumerate(self._split_text_units(chunk_text)):
            start = chunk_text.find(raw_unit, search_start)
            if start == -1:
                start = chunk_text.find(raw_unit)
            if start == -1:
                start = 0
            end = start + len(raw_unit)
            search_start = end

            evidence_kind = self._classify_unit_kind(raw_unit)
            units.append(
                QuestionEvidenceUnit(
                    kind=evidence_kind,
                    text=raw_unit,
                    index=index,
                    start=start,
                    end=end,
                )
            )

        return units

    def choose_best_evidence(
        self,
        evidence_units: list[QuestionEvidenceUnit],
        chunk_type: str | None = None,
    ) -> QuestionEvidenceUnit:
        """按优先级挑选最适合作为当前题目依据的证据单元。"""
        priority_order = {
            "pros_cons": 0,
            "comparison": 1,
            "process": 2,
            "reason": 3,
            "scenario": 4,
            "definition": 5,
            "summary": 6,
        }
        preferred_kind = self._map_chunk_type_to_evidence_kind(chunk_type)
        preferred_units = [unit for unit in evidence_units if unit.kind == preferred_kind] if preferred_kind else []
        candidate_units = preferred_units or evidence_units
        return min(
            candidate_units,
            key=lambda unit: (priority_order.get(unit.kind, 99), unit.index),
        )

    def _classify_unit_kind(self, unit: str) -> str:
        """判断某条证据单元更适合归为哪类题型。"""
        if self._looks_like_pros_cons(unit):
            return "pros_cons"
        if self._looks_like_comparison(unit):
            return "comparison"
        if self._looks_like_process(unit):
            return "process"
        if self._looks_like_reason(unit):
            return "reason"
        if self._looks_like_scenario(unit):
            return "scenario"
        if self._looks_like_definition(unit):
            return "definition"
        return "summary"

    def _split_text_units(self, chunk_text: str) -> list[str]:
        """把正文拆成更容易识别的句子或要点单元。"""
        units: list[str] = []
        for raw_unit in self.split_pattern.split(chunk_text):
            cleaned_unit = self.bullet_prefix_pattern.sub("", raw_unit.strip())
            if cleaned_unit:
                units.append(cleaned_unit)
        return units

    def _looks_like_definition(self, unit: str) -> bool:
        """判断某段文本是否更像定义句。"""
        compact_unit = unit.strip()
        if len(compact_unit) < 6:
            return False
        return self.definition_pattern.search(compact_unit) is not None

    def _looks_like_comparison(self, unit: str) -> bool:
        """判断某段文本是否更像对比句。"""
        return any(keyword in unit for keyword in self.comparison_keywords)

    def _looks_like_pros_cons(self, unit: str) -> bool:
        """判断某段文本是否更像优缺点句。"""
        return any(keyword in unit for keyword in self.pros_cons_keywords)

    def _looks_like_process(self, unit: str) -> bool:
        """判断某段文本是否更像流程步骤句。"""
        return any(keyword in unit for keyword in self.process_keywords)

    def _looks_like_reason(self, unit: str) -> bool:
        """判断某段文本是否更像原因或目的句。"""
        return any(keyword in unit for keyword in self.reason_keywords)

    def _looks_like_scenario(self, unit: str) -> bool:
        """判断某段文本是否更像场景句。"""
        return any(keyword in unit for keyword in self.scenario_keywords)

    def _map_chunk_type_to_evidence_kind(self, chunk_type: str | None) -> str | None:
        """把 chunk 类型映射为更优先的证据类型。"""
        mapping = {
            "definition": "definition",
            "comparison": "comparison",
            "pros_cons": "pros_cons",
            "process": "process",
            "reason": "reason",
            "scenario": "scenario",
            "summary": "summary",
        }
        if not chunk_type:
            return None
        return mapping.get(chunk_type.strip().lower())


question_evidence_service = QuestionEvidenceService()
