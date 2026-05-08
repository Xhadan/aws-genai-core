def batch_embed(texts, batch_size%):
    """Embed multiple texts efficiently."""
    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        batch_embeddings = [get_embedding(text) for text in batch]
        embeddings.extend(batch_embeddings)

    return embeddings

# For larger batches, use async/parallel processing
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def parallel_embed(texts, max_workers):
    """Parallel embedding for large datasets."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop = asyncio.get_event_loop()
        embeddings = await asyncio.gather(*[
            loop.run_in_executor(executor, get_embedding, text)
            for text in texts
        ])
    return embeddings