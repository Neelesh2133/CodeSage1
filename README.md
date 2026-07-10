# 🤖 CodeSage: Automated AI Code Reviewer

CodeSage is an asynchronous FastAPI web service that automates security, style, and performance reviews of code snippets and GitHub Pull Requests using LLMs (OpenRouter API).

---

## ✨ Key Features
- **🔐 JWT Authentication**: Secure signup and login endpoints using bcrypt password hashing and HS256 JWT tokens.
- **📝 Code Snippet Review**: Submit snippets to evaluate them for security vulnerabilities (like SQL injections) or styling bugs.
- **📂 GitHub PR Analysis**: Provide a PR URL, and CodeSage will automatically fetch, filter, and review modified files.
- **🔌 Real-time Webhooks**: Listen for GitHub `pull_request` events to run automated reviews in the background.
- **⚙️ Token-Safe Chunking**: Automatically splits large file diffs to stay safely within LLM context limits.
- **🛡️ Duplicate Prevention**: Webhook review tracker checks commit SHAs to avoid redundant reviews.

---

## 🛠️ Tech Stack
- **FastAPI**: Asynchronous Python web framework.
- **PostgreSQL**: Relational database (with JSONB for structured findings).
- **SQLAlchemy & Alembic**: Database ORM and schema migration manager.
- **OpenRouter (OpenAI SDK)**: LLM client (using the free `nvidia/nemotron-3-ultra-550b-a55b` llm model).
- **Docker Compose**: Containerized database setup.

---

## 🔄 Workflow Summary

### 1. User Authentication
```text
[Client] --- (Signup/Login credentials) ---> [FastAPI /auth Endpoints]
   |                                                    |
[Client] <--- (Bcrypt validation & JWT Token) ----------+
```

### 2. Code Review Flow
```text
[Client Endpoint /reviews/] ---> [FastAPI Router]
                                       |
[PostgreSQL (JSONB Findings)] <--- [LLM Client] <--- [Prompt Builder & Chunking]
```

### 3. Webhook Flow
```text
[GitHub Event] ---> [Webhook Router] -- (Validates HMAC) --> [Immediate 200 OK]
                                                                   |
                                                         [FastAPI BackgroundTask]
                                                                   |
                                                        [Run Review & Save to DB]
```

---

## 🚀 Quick Start Guide

### 1. Environment Setup
Create a `.env` file in the root directory:
```ini
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5433/codesage
OPENROUTER_API_KEY=your-openrouter-key-here
JWT_SECRET=your-secure-jwt-secret-key-here
GITHUB_TOKEN=your-optional-github-pat-here
GITHUB_WEBHOOK_SECRET=your-github-webhook-secret-here
WEBHOOK_REVIEW_USER_EMAIL=webhook-reviewer@codesage.com
```

### 2. Launch the Database
```bash
docker-compose up -d
```

### 3. Run Migrations
```bash
alembic upgrade head
```

### 4. Start CodeSage
```bash
uvicorn app.main:app --reload
```
Interactive API docs are available at `http://localhost:8000/docs`.

---

## 🧪 Running Tests
Verify the installation and logic:
- **Pytest Suite**: `pytest`
- **Mock integration Verification**: `python verify.py`
- **End-to-End Test Client**: `python run_e2e.py`
