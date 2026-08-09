# Compare embeddings on your domain
models = ['titan-embed-v2', 'cohere.embed-english-v3']
for model in models:
    precision = evaluate_context_precision(model, test_queries)
    print(f"{model}: {precision:.3f}")