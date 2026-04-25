# Markdown 解析服务，后续会补结构化解析逻辑。
class MarkdownParserService:
    def parse(self, content: str) -> dict:
        # 先返回最小解析结果，方便后续联调。
        return {
            "title": "Imported Markdown",
            "sections": [],
            "raw_length": len(content),
        }
