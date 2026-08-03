models = [
    'anthropic.claude-3-sonnet-20240229-v1:0',
    'amazon.titan-text-express-v1',
    'meta.llama3-8b-instruct-v1:0'
]

for model in models:
    create_evaluation_job(model, dataset='support-tickets.jsonl')