def demonstrate_overlap(text, chunk_size0, overlap_pct ):
    """Show how overlap works."""
    words = text.split()
    overlap_words = int(chunk_size * overlap_pct / 100)
    step = chunk_size - overlap_words

    chunks = []
    for i in range(0, len(words), step):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append({
            'start': i,
            'end': min(i + chunk_size, len(words)),
            'text': chunk
        })
        if i + chunk_size >= len(words):
            break

    return chunks

# Example: 100 word chunks with 20% overlap
# Chunk 1: words 0-100
# Chunk 2: words 80-180 (20 word overlap)
# Chunk 3: words 160-260 (20 word overlap)