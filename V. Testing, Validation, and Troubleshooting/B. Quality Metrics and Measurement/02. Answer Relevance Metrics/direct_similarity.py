q_embedding = embed(question)
a_embedding = embed(answer)
relevance = cosine_similarity(q_embedding, a_embedding)