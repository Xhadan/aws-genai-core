import boto3
from typing import List, Tuple
import re

class IntelligentChunker:
    """Chunk documents intelligently for optimal context usage"""

    def __init__(self, chunk_sizeP0, chunk_overlapP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_by_semantic_boundaries(self, text: str) -> List[str]:
        """
        Chunk text at semantic boundaries (paragraphs, sections).
        Respects natural document structure.
        """
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if adding paragraph exceeds chunk size
            if len(current_chunk) + len(para) <= self.chunk_size:
                current_chunk += "\n\n" + para if current_chunk else para
            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def chunk_with_overlap(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Create overlapping chunks to preserve context at boundaries.
        Returns list of (chunk_text, start_char, end_char).
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Extend to word boundary
            if end < len(text):
                while end > start and text[end] not in ' \n':
                    end -= 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append((chunk, start, end))

            # Move start with overlap
            start = end - self.chunk_overlap

        return chunks

    def chunk_by_sections(self, text: str, section_markers: List[str] = None) -> List[Dict]:
        """
        Chunk by document sections (headers, numbered sections).
        Returns chunks with section metadata.
        """
        if section_markers is None:
            section_markers = [r'^#{1,6}\s+', r'^\d+\.\s+', r'^[A-Z][A-Z\s]+:']

        # Combine markers into pattern
        pattern = '|'.join(f'({m})' for m in section_markers)

        # Find section boundaries
        sections = []
        last_end = 0
        current_section = None

        for match in re.finditer(pattern, text, re.MULTILINE):
            if current_section:
                sections.append({
                    'title': current_section,
                    'content': text[last_end:match.start()].strip(),
                    'start': last_end,
                    'end': match.start()
                })
            current_section = match.group().strip()
            last_end = match.end()

        # Add final section
        if current_section:
            sections.append({
                'title': current_section,
                'content': text[last_end:].strip(),
                'start': last_end,
                'end': len(text)
            })

        return sections


class ContextRanker:
    """Rank and select most relevant context chunks"""

    def __init__(self, model_id='amazon.titan-embed-text-v1'):
        self.bedrock = boto3.client('bedrock-runtime')
        self.model_id = model_id

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text"""
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=json.dumps({'inputText': text})
        )
        result = json.loads(response['body'].read())
        return result['embedding']

    def rank_chunks(
        self,
        query: str,
        chunks: List[str],
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Rank chunks by relevance to query"""
        import numpy as np

        query_embedding = np.array(self.get_embedding(query))

        scored_chunks = []
        for chunk in chunks:
            chunk_embedding = np.array(self.get_embedding(chunk))
            # Cosine similarity
            similarity = np.dot(query_embedding, chunk_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
            )
            scored_chunks.append((chunk, similarity))

        # Sort by similarity descending
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        return scored_chunks[:top_k]

    def select_context_for_budget(
        self,
        query: str,
        chunks: List[str],
        token_budget: int
    ) -> List[str]:
        """Select highest-ranked chunks that fit in budget"""
        ranked = self.rank_chunks(query, chunks, top_k=len(chunks))

        selected = []
        tokens_used = 0

        for chunk, score in ranked:
            chunk_tokens = len(chunk.split()) * 1.3  # Rough estimate
            if tokens_used + chunk_tokens <= token_budget:
                selected.append(chunk)
                tokens_used += chunk_tokens

        return selected


# Example usage
chunker = IntelligentChunker(chunk_size00, chunk_overlap0)

document = """
# Introduction
This document covers the product specifications and features.

# Technical Specifications
The device measures 10x5x2 inches and weighs 2 pounds.
Battery life is approximately 8 hours under normal usage.

# Features
- Wireless connectivity
- Water resistant
- Voice control support

# Warranty Information
Standard warranty covers 1 year from purchase date.
"""

# Chunk by sections
sections = chunker.chunk_by_sections(document)
print(f"Found {len(sections)} sections")
for section in sections:
    print(f"  - {section['title']}: {len(section['content'])} chars")