# No chunking - entire document as single chunk
no_chunking_config = {
    'chunkingStrategy': 'NONE'
}

# Best for:
# - Short documents (under 300 tokens)
# - FAQs where each Q&A is a document
# - Already chunked content