from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_URL = f"sqlite:///{BASE_DIR / 'interview_review.db'}"
# Markdown 文档默认保存目录。
DOCUMENTS_DIR = BASE_DIR / "storage" / "documents"