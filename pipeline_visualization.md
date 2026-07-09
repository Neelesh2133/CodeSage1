# 🎨 CodeSage Pipeline & Workflow Visualization

To help make CodeSage's internal pipelines easy to understand, we have generated a high-fidelity visual architecture diagram and broken it down using simple real-world analogies.

## 🖼️ System Architecture Diagram

![CodeSage Architecture Infographic](C:/Users/csbot/.gemini/antigravity-ide/brain/f8754842-7980-4bcd-838d-effeb53e792d/codesage_pipelines_1783524957205.png)

---

## 🔑 1. User Authentication Pipeline

> [!NOTE]
> **Analogy**: Think of this as getting a VIP Wristband at a concert.
> - **Signup**: You register your name (email) and establish a password.
> - **Login**: You show your credentials, and the concert hosts hand you a signed **Wristband** (the JWT token) with your User ID stamped on it.
> - **Requests**: Every time you want to get into the VIP lounge (protected routes like submitting code reviews), you simply show the wristband.

### Step-by-Step Flow:
1. **Signup**:
   - The user calls `POST /auth/signup` with an email and password.
   - Password is encrypted using `bcrypt` (scrambled so it cannot be read in plain-text if the database is leaked).
   - Saved to the **Users Table** in PostgreSQL.
2. **Login**:
   - User calls `POST /auth/login` sending their email and password.
   - The application checks the database, validates the password hash, and creates a JWT (JSON Web Token) token signed with a secret key (`HS256`).
   - The token contains the user's ID (`sub`) and an expiration date (valid for 1 day).
3. **Usage**:
   - For all subsequent API calls (such as reviewing code), the client adds `Authorization: Bearer <token>` in the HTTP headers.
   - The application decrypts and verifies the token on the fly. If valid, the request proceeds; if invalid or expired, it returns `401 Unauthorized` instantly.

---

## 🤖 2. Automated Code Review Pipeline (Manual Code Snippet)

> [!NOTE]
> **Analogy**: Think of this as submitting a draft essay to a strict grammar checker.
> - **Submission**: You send the text.
> - **Formatting**: The tool wraps the essay with grading guidelines (System Prompts).
> - **LLM Query**: It sends it to the AI reviewer.
> - **Defensive Check**: If the AI formats the feedback incorrectly, the tool asks the AI to format it again (retry loop).
> - **Archival**: The final report is saved to a folder (database) and handed to you.

### Step-by-Step Flow:
1. **Request**:
   - Client sends code to `POST /reviews/` containing the raw snippet.
2. **System Prompt Wrapping**:
   - CodeSage builds a package containing the user's code, preceded by a strict instruction telling the AI to output *only* a JSON array containing findings (file, line number, category, severity, message, and suggestion).
3. **LLM Submission (OpenRouter)**:
   - The request hits OpenRouter. OpenRouter directs it to the free `nvidia/nemotron-3-ultra-550b-a55b:free` model.
4. **Output Verification (Parsing Retry Loop)**:
   - The system reads the AI's response text.
   - It strips any Markdown formatting code blocks (like ` ```json ` and ` ``` `).
   - It attempts to parse it into a standard JSON array.
   - **Retry Handling**: If the AI breaks the output format (returns raw English instead of JSON), the loop runs **one more time** to request a correction. If it fails twice, it returns an HTTP `502 Bad Gateway` showing the raw unparseable text.
5. **Persistence**:
   - Once successfully parsed, the structured JSON list is written to the **Reviews Table** (bound to the User ID) and returned to the client.

---

## 📂 3. GitHub Pull Request (PR) URL Review Pipeline

> [!NOTE]
> **Analogy**: Think of this as inviting a proofreader to review only the pages you changed in a textbook.
> - **Locating pages**: You supply the PR URL (e.g. Chapter 4 changes). The code parses the URL to find the book and chapter.
> - **Fetching changes**: It calls GitHub to download the diff (the specific lines added or removed).
> - **Safety filtering**: It skips heavy illustrations or binary images (skipped files) and tells you about them (warnings).
> - **Splitting Chapters**: If you changed too many files, it divides them into smaller packets so the proofreader doesn't get overwhelmed (chunking).

### Step-by-Step Flow:
1. **API Trigger**:
   - User calls `POST /reviews/pr` with a GitHub PR URL (e.g. `https://github.com/owner/repo/pull/1`).
2. **GitHub API Query**:
   - CodeSage calls GitHub's API to fetch the files modified in that PR.
3. **Patch Extraction**:
   - For each file, it retrieves the unified Git diff patch (lines changed).
   - If a file is binary (like a `.png` image) or too large to diff, GitHub won't provide a patch. CodeSage tracks these skipped files as `warnings`.
4. **Token-Safe Chunking**:
   - Standard AI models have a token ceiling. If the combined text size of all files exceeds ~8000 tokens (32,000 characters), `app/chunking.py` splits them into parts (e.g. `file_1.py (part 1)`) and aggregates smaller files into groups.
5. **LLM Reviews**:
   - CodeSage sends the structured diff patches to the AI.
   - It parses findings, appends warning notices about any skipped binary files, saves the review, and returns it to the user.

---

## 🔌 4. GitHub Webhooks Pipeline (Real-time Event Listening)

> [!NOTE]
> **Analogy**: Think of a automated security guard watching a turnstile.
> - **Event**: Someone walks through the turnstile (submits/updates a PR).
> - **Validation**: The guard verifies the sender's ID card (HMAC Signature).
> - **Immediate Response**: The guard says "Access Granted" and logs the entry immediately (HTTP 200), so the turnstile doesn't freeze.
> - **Background Work**: While the turnstile keeps spinning, the guard goes to run a background check on the visitor in the office (FastAPI BackgroundTasks).
> - **Double-Check**: If the guard already ran a check on this exact person earlier (same Commit SHA), they skip the work to save time.

### Step-by-Step Flow:
1. **GitHub Trigger**:
   - A developer pushes code or opens a PR on GitHub. GitHub fires a POST request to `/webhooks/github` containing the payload.
2. **Signature Verification**:
   - CodeSage receives the payload alongside an `X-Hub-Signature-256` header.
   - It computes the HMAC-SHA256 signature of the payload using the secret shared key (`GITHUB_WEBHOOK_SECRET`) and compares it using constant-time comparison to prevent timing attacks.
3. **Event Filtering**:
   - It filters out non-PR events. It only reviews actions: `opened`, `synchronize` (code updated), or `reopened`.
4. **FastAPI Background Dispatch**:
   - If it's a valid PR action, CodeSage schedules the review function `process_pr_review` to run in the background.
   - It immediately returns `{"status": "accepted"}` to GitHub (takes < 5ms), preventing GitHub connection timeouts.
5. **Deduplication Check**:
   - Inside the background task, the worker queries PostgreSQL to check if a review for this specific Repository, PR number, and Commit SHA already exists.
   - If it does, the worker terminates immediately to avoid wasting LLM API credits.
6. **Execution**:
   - If unique, the worker fetches the files, chunks them, queries the LLM, and logs the result under a dedicated webhook reviewer user account.
