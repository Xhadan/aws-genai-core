from jsonschema import validate
schema = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["answer"]
}
validate(instance=response_json, schema=schema)