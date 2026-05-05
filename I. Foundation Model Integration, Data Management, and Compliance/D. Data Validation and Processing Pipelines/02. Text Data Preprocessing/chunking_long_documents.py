from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_document(text, chunk_size00, chunk_overlap 0):
    """Chunk document for RAG knowledge base."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_text(text)
    return chunks

# For fine-tuning: token-based chunking
def chunk_by_tokens(text, tokenizer, max_tokensQ2, overlap_tokensP):
    """Chunk by token count for training data."""
    tokens = tokenizer.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        start = end - overlap_tokens

    return chunks