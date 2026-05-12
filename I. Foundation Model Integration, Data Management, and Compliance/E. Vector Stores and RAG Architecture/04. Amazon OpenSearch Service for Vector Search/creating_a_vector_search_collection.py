import boto3
import json

aoss_client = boto3.client('opensearchserverless')

# Step 1: Create encryption policy
aoss_client.create_security_policy(
    name='vector-encryption-policy',
    type='encryption',
    policy=json.dumps({
        "Rules": [
            {
                "Resource": ["collection/my-vector-collection"],
                "ResourceType": "collection"
            }
        ],
        "AWSOwnedKey": True
    })
)

# Step 2: Create network policy
aoss_client.create_security_policy(
    name='vector-network-policy',
    type='network',
    policy=json.dumps([
        {
            "Rules": [
                {
                    "Resource": ["collection/my-vector-collection"],
                    "ResourceType": "collection"
                }
            ],
            "AllowFromPublic": True  # Or use VPC endpoint
        }
    ])
)

# Step 3: Create data access policy
aoss_client.create_access_policy(
    name='vector-access-policy',
    type='data',
    policy=json.dumps([
        {
            "Rules": [
                {
                    "Resource": ["collection/my-vector-collection"],
                    "Permission": [
                        "aoss:CreateCollectionItems",
                        "aoss:UpdateCollectionItems",
                        "aoss:DescribeCollectionItems"
                    ],
                    "ResourceType": "collection"
                },
                {
                    "Resource": ["index/my-vector-collection/*"],
                    "Permission": [
                        "aoss:CreateIndex",
                        "aoss:UpdateIndex",
                        "aoss:DescribeIndex",
                        "aoss:ReadDocument",
                        "aoss:WriteDocument"
                    ],
                    "ResourceType": "index"
                }
            ],
            "Principal": ["arn:aws:iam::123456789012:role/MyRole"]
        }
    ])
)

# Step 4: Create collection
collection_response = aoss_client.create_collection(
    name='my-vector-collection',
    type='VECTORSEARCH',
    description='Vector store for RAG application'
)

collection_id = collection_response['createCollectionDetail']['id']