class Expected(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]

result = Expected.model_validate(json.loads(response))