import json
import jsonschema

TRAINING_DATA_SCHEMA = {
    "type": "object",
    "required": ["prompt", "completion"],
    "properties": {
        "prompt": {"type": "string", "minLength": 10, "maxLength": 4096},
        "completion": {"type": "string", "minLength": 1, "maxLength": 2048}
    }
}

def lambda_handler(event, context):
    """Validate training data against schema."""
    s3_path = event['inputPath']
    # Download and validate each record...

    validation_errors = []
    total_records = 0
    valid_records = 0

    # Validate records (simplified)
    for record in get_records(s3_path):
        total_records += 1
        try:
            jsonschema.validate(record, TRAINING_DATA_SCHEMA)
            valid_records += 1
        except jsonschema.ValidationError as e:
            validation_errors.append(str(e))

    schema_valid = len(validation_errors) = 0
    validity_ratio = valid_records / total_records if total_records > 0 else 0

    return {
        'schemaValid': schema_valid,
        'validityRatio': validity_ratio,
        'totalRecords': total_records,
        'errorCount': len(validation_errors),
        'inputPath': s3_path
    }