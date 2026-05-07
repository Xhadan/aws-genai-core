from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.wrangler import DataWrangler

# Reference the Data Wrangler flow
flow_uri = 's3://my-bucket/data-wrangler-flows/training-prep.flow'

processor = DataWrangler(
    role=role,
    instance_count=2,
    instance_type='ml.m5.4xlarge',
    sagemaker_session=session,
    flow=flow_uri,
    volume_size_in_gb0
)

# Run the flow
processor.run(
    inputs=[
        ProcessingInput(
            source='s3://my-bucket/raw-training-data/',
            destination='/opt/ml/processing/input'
        )
    ],
    outputs=[
        ProcessingOutput(
            source='/opt/ml/processing/output',
            destination='s3://my-bucket/processed-training-data/'
        )
    ]
)