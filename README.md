# interview-review-assistant

An AI-powered interview review assistant that turns Markdown notes into quizzes, schedules daily review, and tracks mastery.

## Tech Stack

- Backend: FastAPI + SQLModel + SQLite
- Frontend: Vue 3 + Vite + Vue Router
- Document parsing: Markdown-first
- AI enhancement: DeepSeek API (planned)

## Current Scope

This repository is scaffolded around the MVP workflow:

1. Import Markdown interview notes
2. Parse notes into knowledge chunks
3. Generate rule-based questions
4. Schedule daily review tasks
5. Track progress and wrong questions

## Project Structure

```text
backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
frontend/
  src/
    components/
    router/
    views/
面经复习软件-详细进度安排.md
```

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
