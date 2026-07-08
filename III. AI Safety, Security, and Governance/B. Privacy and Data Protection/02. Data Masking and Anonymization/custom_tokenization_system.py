import boto3
import uuid
import hashlib
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
kms = boto3.client('kms')

class TokenizationService:
    """
    Secure tokenization service using DynamoDB and KMS.
    """

    def __init__(self, table_name, kms_key_id):
        self.table = dynamodb.Table(table_name)
        self.kms_key_id = kms_key_id

    def _generate_token(self):
        """Generate random token."""
        return f"TKN_{uuid.uuid4().hex[:16].upper()}"

    def _encrypt(self, plaintext):
        """Encrypt value with KMS."""
        response = kms.encrypt(
            KeyId=self.kms_key_id,
            Plaintext=plaintext.encode()
        )
        return response['CiphertextBlob']

    def _decrypt(self, ciphertext):
        """Decrypt value with KMS."""
        response = kms.decrypt(
            KeyId=self.kms_key_id,
            CiphertextBlob=ciphertext
        )
        return response['Plaintext'].decode()

    def tokenize(self, value, data_type='GENERIC'):
        """
        Tokenize a sensitive value.
        Returns existing token if value was previously tokenized.
        """
        # Create hash of value for lookup (don't store plaintext for lookup)
        value_hash = hashlib.sha256(value.encode()).hexdigest()

        # Check if already tokenized
        try:
            response = self.table.get_item(
                Key={'value_hash': value_hash}
            )
            if 'Item' in response:
                return response['Item']['token']
        except ClientError:
            pass

        # Generate new token
        token = self._generate_token()
        encrypted_value = self._encrypt(value)

        # Store mapping
        self.table.put_item(
            Item={
                'value_hash': value_hash,
                'token': token,
                'encrypted_value': encrypted_value,
                'data_type': data_type,
                'created_at': str(boto3.utils.datetime.datetime.utcnow())
            }
        )

        return token

    def detokenize(self, token):
        """
        Retrieve original value from token.
        Requires proper IAM permissions.
        """
        # Query by token (need GSI on token)
        response = self.table.query(
            IndexName='token-index',
            KeyConditionExpression='#t = :token',
            ExpressionAttributeNames={'#t': 'token'},
            ExpressionAttributeValues={':token': token}
        )

        if not response['Items']:
            raise ValueError(f"Token not found: {token}")

        encrypted_value = response['Items'][0]['encrypted_value']
        return self._decrypt(encrypted_value.value)

# Usage
tokenizer = TokenizationService(
    table_name='tokenization-vault',
    kms_key_id='alias/tokenization-key'
)

# Tokenize sensitive data
ssn = "123-45-6789"
token = tokenizer.tokenize(ssn, data_type='SSN')
print(f"Token: {token}")  # TKN_A1B2C3D4E5F6G7H8

# Later, retrieve original (requires authorization)
original = tokenizer.detokenize(token)
print(f"Original: {original}")  # 123-45-6789