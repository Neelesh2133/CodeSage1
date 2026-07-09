# CodeSage Project Analysis and Architecture Decisions

This document details the pipeline, runtime workflow, and design decisions of the **CodeSage** automated code review application.

---

## 1. Runtime Workflows & Pipelines

CodeSage exposes two main workflows: **Authentication** and **Automated Code Review**.

### A. Authentication Pipeline
The application uses standard OAuth2 with password bearer flow and JWT (JSON Web Tokens) to secure endpoints.

```
sequenceDiagram
    actor User as Client
    participant AuthRouter as Auth Router (API)
    participant AuthDB as Database (PostgreSQL)

    Signup Flow:
    User -> POST /auth/signup (email, password) -> AuthRouter
    AuthRouter -> Hash password with bcrypt -> AuthRouter
    AuthRouter -> Insert User record -> AuthDB
    AuthRouter -> Return User ID and Email -> User

    Login Flow:
    User -> POST /auth/login (form-data: username, password) -> AuthRouter
    AuthRouter -> Retrieve user by email -> AuthDB
    AuthRouter -> Verify bcrypt hash -> AuthRouter
    AuthRouter -> Sign JWT token -> AuthRouter
    AuthRouter -> Return access_token & token_type -> User
```

1. **Signup (`POST /auth/signup`)**:
   - Receives JSON payload with `email` (validated via Pydantic `EmailStr`) and `password`.
   - Hashes the password using `bcrypt` (via `passlib.context.CryptContext`).
   - Inserts the new `User` record into PostgreSQL.
2. **Login (`POST /auth/login`)**:
   - Expects standard `x-www-form-urlencoded` fields (`username` and `password`) to support standard OAuth2 clients.
   - Fetches the user from PostgreSQL, verifies the hash, and generates a JWT signed with `HS256` containing the user ID as the subject (`sub`).
3. **Dependency Injection (`get_current_user`)**:
   - Secures downstream endpoints. It extracts the Bearer token from the `Authorization` header, decodes it, verifies its signature and expiration, and fetches the current user from the database.

---

### B. Automated Code Review Pipeline
Once authenticated, users can submit code snippets for security, style, and performance reviews.

```
Request Flow:
Client Request (POST /reviews/ + JWT) -> get_current_user Dependency
  |
  +-> Valid -> LLM Client (OpenRouter API)
  |              |
  |              +-> Attempt 1: Parse JSON -> Success?
  |                    |               |
  |                    | (No)          +-> (Yes) -> Save to DB -> Return Response
  |                    v
  |                  Attempt 2: Retry LLM Request -> Success?
  |                    |               |
  |                    | (No)          +-> (Yes) -> Save to DB -> Return Response
  |                    v
  |                  Return 502 Bad Gateway + Raw LLM Output
  |
  +-> Invalid/Missing Token -> Return 401 Unauthorized
```

1. **Client Submission**: The client sends a `POST /reviews/` request with the code snippet in the request body and the JWT in the `Authorization` header.
2. **LLM Interaction**: The `review_code` function issues a request to OpenRouter (`nvidia/nemotron-3-ultra-550b-a55b:free` model) with a structured `SYSTEM_PROMPT` instructing the model to output a strict JSON array of finding objects.
3. **Defensive Parsing & Retry Loop**:
   - The helper defensively removes markdown fences (e.g. ` ```json `) since some models add them despite system instructions.
   - If `json.loads` fails, it catches `json.JSONDecodeError` and **retries once**.
   - If both attempts fail to produce valid JSON, it throws `LLMReviewError`.
4. **Error Handling**: The reviews router catches `LLMReviewError` and returns an **HTTP 502 Bad Gateway** response showing the `raw_response` from the LLM for immediate debugging.
5. **Database Persistence**: On success, the findings and snippet are saved to the PostgreSQL `Review` table, linked to the `user_id`.

---

## 2. Design Decisions: Why We Used This Instead of That

### 🚀 FastAPI vs. Flask / Django
* **Why FastAPI?** 
  * FastAPI provides native support for **Pydantic** validation out-of-the-box. This ensures input parameters and database responses strictly adhere to defined schemas.
  * It auto-generates interactive API documentation (Swagger UI at `/docs`), which is invaluable for testing authentication flows.
  * It is fully asynchronous and achieves significantly better performance compared to synchronous alternatives like Flask.

### 🔐 OAuth2 Password Bearer vs. Custom Auth Headers
* **Why OAuth2 Password Bearer?**
  * It integrates seamlessly with FastAPI's `Depends(oauth2_scheme)`.
  * Using standard OAuth2 flows enables Swagger UI's built-in **"Authorize"** button (padlock). Developers can log in through the Swagger UI, and the token is automatically added to all requests under the hood.

### 🐘 PostgreSQL & SQLAlchemy vs. MongoDB / NoSQL
* **Why PostgreSQL?**
  * The data model has a clear relational hierarchy: Users own Reviews, and Reviews contain a fixed JSON schema of findings.
  * Relational databases enforce schema integrity and foreign key constraints (e.g., ensuring reviews are always linked to a valid user and cascading deletion works correctly).
  * PostgreSQL natively supports `JSONB` data types (used in the `findings` column), combining relational schema stability with flexible JSON storage for AI findings.

### 🤖 OpenRouter & Nemotron vs. Direct OpenAI/Anthropic SDKs
* **Why OpenRouter?**
  * OpenRouter uses the standard `openai` Python SDK syntax, meaning the codebase remains highly compatible and can switch backend model endpoints (e.g. to OpenAI, Anthropic, or DeepSeek) with a simple model name string change in `llm_client.py`.
  * The `nvidia/nemotron-3-ultra-550b-a55b:free` model is free and highly capable, making it ideal for development and testing.

### 🧪 Standalone Test Script vs. Pytest Suite
* **Why both?**
  * **Pytest (`test_api.py`)** is ideal for automated CI/CD and regression testing. It tests endpoints in-process (using `TestClient`), mocks nothing, and validates API behavior like correct error codes (401 on missing token, login rejection).
  * **Interactive CLI Script (`test_reviews.py`)** is designed for hands-on, live integration validation. It lets developers hit either the in-process API or a live deployed staging URL, printing out beautifully formatted, colorized findings to the terminal.
