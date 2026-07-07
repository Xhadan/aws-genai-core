import boto3

databrew = boto3.client('databrew')

def create_masking_recipe(recipe_name):
    """
    Create DataBrew recipe for PII masking.
    """
    response = databrew.create_recipe(
        Name=recipe_name,
        Steps=[
            # Mask SSN - keep last 4
            {
                'Action': {
                    'Operation': 'CRYPTOGRAPHIC_HASH',
                    'Parameters': {
                        'sourceColumn': 'ssn',
                        'secretManagerArn': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:hash-key'
                    }
                }
            },
            # Mask credit card
            {
                'Action': {
                    'Operation': 'REPLACE_WITH_CONSTANT',
                    'Parameters': {
                        'sourceColumn': 'credit_card',
                        'value': 'XXXX-XXXX-XXXX-0000'
                    }
                }
            },
            # Generalize age to ranges
            {
                'Action': {
                    'Operation': 'BIN_BY_SIZE',
                    'Parameters': {
                        'sourceColumn': 'age',
                        'binSize': '10',
                        'targetColumn': 'age_range'
                    }
                }
            },
            # Hash email for pseudonymization
            {
                'Action': {
                    'Operation': 'CRYPTOGRAPHIC_HASH',
                    'Parameters': {
                        'sourceColumn': 'email',
                        'secretManagerArn': 'arn:aws:secretsmanager:us-east-1:123456789012:secret:hash-key'
                    }
                }
            }
        ]
    )
    return response

def run_masking_job(dataset_name, recipe_name, output_bucket):
    """
    Run DataBrew job to apply masking recipe.
    """
    response = databrew.create_recipe_job(
        Name=f'{dataset_name}-masking-job',
        DatasetNametaset_name,
        RecipeReference={
            'Name': recipe_name,
            'RecipeVersion': 'LATEST_PUBLISHED'
        },
        Outputs=[
            {
                'Location': {
                    'Bucket': output_bucket,
                    'Key': f'masked-data/{dataset_name}/'
                },
                'Format': 'PARQUET',
                'Overwrite': True
            }
        ],
        RoleArn='arn:aws:iam::123456789012:role/DataBrewRole'
    )
    return response