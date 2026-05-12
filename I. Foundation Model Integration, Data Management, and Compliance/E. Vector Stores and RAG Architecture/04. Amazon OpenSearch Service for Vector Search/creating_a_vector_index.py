from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

# Get credentials
credentials = boto3.Session().get_credentials()
region = 'us-east-1'
service = 'aoss'

awsauth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token
)

# Connect to OpenSearch Serverless
host = 'abc123xyz.us-east-1.aoss.amazonaws.com'  # Collection endpoint

client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

# Create vector index with HNSW
index_body = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 512
        }
    },
    "mappings": {
        "properties": {
            "embedding": {
                "type": "knn_vector",
                "dimension": 1024,  # Match Titan Embeddings V2
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",  # Or l2, innerproduct
                    "engine": "lucene",
                    "parameters": {
                        "ef_construction": 512,
                        "m": 16
                    }
                }
            },
            "text": {
                "type": "text"
            },
            "metadata": {
                "type": "object"
            }
        }
    }
}

client.indices.create(index='rag-vectors', body=index_body)