{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "count": {"type": "integer"},
    "active": {"type": "boolean"},
    "tags": {
      "type": "array",
      "items": {"type": "string"}
    }
  },
  "required": ["name", "count"]
}