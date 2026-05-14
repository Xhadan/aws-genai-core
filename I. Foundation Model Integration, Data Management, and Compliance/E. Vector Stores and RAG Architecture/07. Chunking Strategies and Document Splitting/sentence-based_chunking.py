import nltk
from nltk.tokenize import sent_tokenize

nltk.download('punkt')

def sentence_chunking(text, max_sentences=5, overlap_sentences=1):
    """Chunk text by sentences with overlap."""
    sentences = sent_tokenize(text)
    chunks = []

    i = 0
    while i < len(sentences):
        chunk_sentences = sentences[i:i + max_sentences]
        chunk = ' '.join(chunk_sentences)
        chunks.append({
            'text': chunk,
            'start_sentence': i,
            'end_sentence': min(i + max_sentences, len(sentences))
        })
        i += max_sentences - overlap_sentences

    return chunks

# Example usage
text = """
Amazon Bedrock is a fully managed service. It provides access to foundation models.
You can use it for text generation. It also supports embeddings.
Knowledge Bases enable RAG workflows. They handle chunking automatically.
"""

chunks = sentence_chunking(text, max_sentences=3, overlap_sentences=1)
for chunk in chunks:
    print(f"Sentences {chunk['start_sentence']}-{chunk['end_sentence']}: {chunk['text'][:80]}...")