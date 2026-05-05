-- Rules for fine-tuning dataset validation
Rules = [
    -- Completeness: No empty fields
    Completeness "prompt" >= 1.0,
    Completeness "completion" >= 1.0,

    -- Validity: Field length within model limits
    ColumnLength "prompt" between 10 and 4096,
    ColumnLength "completion" between 1 and 2048,

    -- Uniqueness: No duplicate training examples
    IsUnique "prompt",

    -- Accuracy: No NULL values
    ColumnValues "prompt" != NULL,
    ColumnValues "completion" != NULL,

    -- Custom: JSON format validation
    CustomSql "SELECT COUNT(*) FROM primary WHERE TRY(JSON_PARSE(prompt)) IS NULL" = 0
]