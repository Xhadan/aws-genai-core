import asyncio
from concurrent.futures import ThreadPoolExecutor

async def parallel_rag_queries(queries, knowledge_base_id, max_workers=5):
    """
    Execute multiple RAG queries in parallel.
    """
    async def execute_query(query):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            response = await loop.run_in_executor(
                executor,
                lambda: bedrock_agent_runtime.retrieve_and_generate(
                    input={'text': query},
                    retrieveAndGenerateConfiguration={
                        'type': 'KNOWLEDGE_BASE',
                        'knowledgeBaseConfiguration': {
                            'knowledgeBaseId': knowledge_base_id,
                            'modelArn': 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0'
                        }
                    }
                )
            )
        return {'query': query, 'response': response['output']['text']}

    tasks = [execute_query(q) for q in queries]
    results = await asyncio.gather(*tasks)
    return results