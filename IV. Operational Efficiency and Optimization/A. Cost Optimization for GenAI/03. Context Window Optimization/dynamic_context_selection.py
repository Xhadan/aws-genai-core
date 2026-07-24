# Instead of:
context = full_document_text  # 50K tokens

# Use:
relevant_chunks = vector_search(query, top_k=5)  # 2K tokens
context = "\n".join(relevant_chunks)