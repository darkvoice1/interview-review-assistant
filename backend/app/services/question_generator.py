# 规则题目生成服务。
class QuestionGeneratorService:
    def generate_from_chunk(self, chunk_text: str) -> list[dict]:
        # 空内容不生成题目。
        if not chunk_text.strip():
            return []

        # 先生成一条基础短答题作为占位实现。
        return [
            {
                "question_type": "short_answer",
                "question": f"请概括以下知识点的核心内容：{chunk_text[:20]}",
                "answer": chunk_text[:120],
                "difficulty": 1,
            }
        ]
