import re

def paragraph_chunking(text, max_paragraphs=2, merge_short=True, min_length0):
    """Chunk text by paragraphs."""
    # Split by double newlines or markdown headers
    paragraphs = re.split(r'\n\n+|(?=^#{1,3}\s)', text, flags=re.MULTILINE)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para_length = len(para)

        # Merge short paragraphs
        if merge_short and current_length + para_length < min_length:
            current_chunk.append(para)
            current_length += para_length
        elif len(current_chunk) < max_paragraphs:
            current_chunk.append(para)
            current_length += para_length
        else:
            # Save current chunk and start new one
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_length = para_length

    # Don't forget the last chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks