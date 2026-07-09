def build_diff_prompt(files: list[dict]) -> str:
    """Combines per-file patches into a single labeled diff block for the LLM."""
    parts = []
    skipped = []
    for f in files:
        patch = f.get("patch")
        if not patch:
            skipped.append(f["filename"])  # binary files or too-large diffs have no patch
            continue
        parts.append(f"### File: {f['filename']}\n```diff\n{patch}\n```")

    if skipped:
        parts.append(f"\n(Note: {len(skipped)} file(s) skipped — binary or too large to diff: {', '.join(skipped)})")

    return "\n\n".join(parts)