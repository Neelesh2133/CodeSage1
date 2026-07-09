import json
from openai import OpenAI
from app.config import settings

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openrouter_api_key
)

SYSTEM_PROMPT = """You are a strict senior code reviewer. Analyze the given code and return ONLY a JSON array of findings. No prose, no markdown fences, no explanation — just the raw JSON array.

The input may contain multiple files marked with "### File: <path>" headers followed by unified diffs. When this is the case, set "file_path" to the exact path from the matching header, and use the diff's line numbers where determinable (otherwise null).

Each finding must match this schema:
{
  "file_path": string or null,
  "line_number": integer or null,
  "severity": "critical" | "high" | "medium" | "low" | "info",
  "category": "bug" | "security" | "performance" | "style" | "maintainability",
  "message": string,
  "suggestion": string or null
}

If there are no issues, return an empty array []."""

class LLMReviewError(Exception):
    def __init__(self, message: str, raw_response: str):
        super().__init__(message)
        self.raw_response = raw_response


def review_code(code: str) -> list[dict]:
    last_error = None
    last_raw = ""
    for attempt in range(2):
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b:free",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": code}
            ],
            temperature=0.2
        )
        raw = response.choices[0].message.content.strip()
        # Models sometimes wrap JSON in ```json fences despite instructions — strip defensively
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            last_error = e
            last_raw = raw
            # Loops and retries once

    raise LLMReviewError(f"LLM returned malformed JSON: {last_error}", last_raw)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openrouter_api_key,
    timeout=30.0
)    