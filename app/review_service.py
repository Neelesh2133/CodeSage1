from app.chunking import chunk_units
from app.llm_client import review_code, LLMReviewError
import openai

def build_prompt(units: list[tuple[str, str]]) -> str:
    parts = []
    for label, text in units:
        parts.append(f"### File: {label}\n```diff\n{text}\n```" if label else f"```\n{text}\n```")
    return "\n\n".join(parts)

def review_units(units: list[tuple[str, str]]) -> tuple[list[dict], list[str]]:
    """Runs the review pipeline across one or more chunks.
    Returns (all_findings, warnings) — warnings note chunking, skipped files, or partial failures."""
    chunks = chunk_units(units)
    all_findings: list[dict] = []
    warnings: list[str] = []

    if len(chunks) > 1:
        warnings.append(f"Large input split into {len(chunks)} chunks for review")

    for i, chunk in enumerate(chunks, start=1):
        prompt_text = build_prompt(chunk)
        try:
            findings = review_code(prompt_text)
            all_findings.extend(findings)
        except (LLMReviewError, openai.OpenAIError):
            raise
        except Exception as e:
            warnings.append(f"Chunk {i}/{len(chunks)} failed and was skipped: {e}")

    return all_findings, warnings