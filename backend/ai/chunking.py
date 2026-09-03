MAX_CHUNK_CHARS = 800
OVERLAP_CHARS = 120


def _split_long_paragraph(paragraph, max_length, overlap):
    chunks = []
    start = 0
    while start < len(paragraph):
        end = min(start + max_length, len(paragraph))
        if end < len(paragraph):
            boundary = paragraph.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunks.append(paragraph[start:end].strip())
        if end >= len(paragraph):
            break
        start = max(end - overlap, start + 1)
    return [chunk for chunk in chunks if chunk]


def chunk_text(text, max_length=MAX_CHUNK_CHARS, overlap=OVERLAP_CHARS):
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_length:
        return [text]
    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
    chunks = []
    current = ""
    for paragraph in paragraphs:
        pieces = [paragraph]
        if len(paragraph) > max_length:
            pieces = _split_long_paragraph(paragraph, max_length, overlap)
        for piece in pieces:
            candidate = f"{current}\n{piece}" if current else piece
            if len(candidate) <= max_length:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = piece
    if current:
        chunks.append(current)
    return chunks
