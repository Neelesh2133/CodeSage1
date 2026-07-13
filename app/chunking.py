CHARS_PER_TOKEN = 4  # rough heuristic — good enough for chunk sizing, not billing
MAX_CHUNK_TOKENS = 8000 #token limit
MAX_CHUNK_CHARS = MAX_CHUNK_TOKENS * CHARS_PER_TOKEN

def _split_large_unit(label: str, text: str) -> list[tuple[str, str]]:
    """Splits a single oversized file/snippet into line-based sub-chunks."""
    lines = text.splitlines(keepends=True)
    sub_chunks, current, current_len, part = [], [], 0, 1
    for line in lines:
        if current_len + len(line) > MAX_CHUNK_CHARS and current:
            sub_chunks.append((f"{label} (part {part})", "".join(current)))
            current, current_len, part = [], 0, part + 1
        current.append(line)
        current_len += len(line)
    if current:
        sub_chunks.append((f"{label} (part {part})" if part > 1 else label, "".join(current)))
    return sub_chunks

def chunk_units(units: list[tuple[str, str]]) -> list[list[tuple[str, str]]]:
    """Groups (label, text) units into chunks, each under MAX_CHUNK_CHARS.
    A single unit larger than the limit gets split into labeled sub-parts first."""
    expanded = []
    for label, text in units:
        if len(text) > MAX_CHUNK_CHARS:
            expanded.extend(_split_large_unit(label, text))
        else:
            expanded.append((label, text))

    chunks, current_chunk, current_len = [], [], 0
    for label, text in expanded:
        if current_len + len(text) > MAX_CHUNK_CHARS and current_chunk:
            chunks.append(current_chunk)
            current_chunk, current_len = [], 0
        current_chunk.append((label, text))
        current_len += len(text)
    if current_chunk:
        chunks.append(current_chunk)
    return chunks
