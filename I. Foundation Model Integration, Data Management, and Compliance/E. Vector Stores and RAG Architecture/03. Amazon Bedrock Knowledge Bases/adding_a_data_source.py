# Step 2: Create Data Source
ds_response = bedrock_agent.create_data_source(
    knowledgeBaseId=kb_id,
    name='company-docs',
    dataSourceConfiguration={
        's3Configuration': {
            'bucketArn': 'arn:aws:s3:::my-documents-bucket',
            'inclusionPrefixes': ['documents/', 'policies/']
        }
    },
    vectorIngestionConfiguration={
        'chunkingConfiguration': {
            'chunkingStrategy': 'SEMANTIC',
            'semanticChunkingConfiguration': {
                'maxTokens': 512,
                'bufferSize': 0,
                'breakpointPercentileThreshold': 95
            }
        }
    }
)

data_source_id = ds_response['dataSource']['dataSourceId']

# Step 3: Start Ingestion
bedrock_agent.start_ingestion_job(
    knowledgeBaseId=kb_id,
    dataSourceIdta_source_id
)