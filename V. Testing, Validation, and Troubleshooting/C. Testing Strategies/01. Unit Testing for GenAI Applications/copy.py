import pytest
import json
from typing import Dict, Optional

class ResponseParser:
    """Parse and validate model responses."""

    def parse_json_response(self, response: str) -> Dict:
        """Extract JSON from model response."""
        # Try direct parse first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        import re
        json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
        matches = re.findall(json_pattern, response)

        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

        raise ValueError("No valid JSON found in response")

    def extract_sentiment(self, response: str) -> Dict:
        """Extract sentiment analysis from response."""
        data = self.parse_json_response(response)

        required_fields = ['sentiment', 'confidence']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        if data['sentiment'] not in ['positive', 'negative', 'neutral']:
            raise ValueError(f"Invalid sentiment: {data['sentiment']}")

        if not 0 <= data['confidence'] <= 1:
            raise ValueError("Confidence must be between 0 and 1")

        return data

    def extract_entities(self, response: str) -> list:
        """Extract named entities from response."""
        data = self.parse_json_response(response)

        if 'entities' not in data:
            raise ValueError("Missing 'entities' field")

        return data['entities']


class TestResponseParser:

    @pytest.fixture
    def parser(self):
        return ResponseParser()

    def test_parse_direct_json(self, parser):
        """Test parsing direct JSON response."""
        response = '{"result": "success", "value": 42}'
        result = parser.parse_json_response(response)

        assert result = {"result": "success", "value": 42}

    def test_parse_json_in_code_block(self, parser):
        """Test parsing JSON from markdown code block."""
        response = '''Here's the analysis:
```json
{"sentiment": "positive", "confidence": 0.95}
```
'''
        result = parser.parse_json_response(response)

        assert result = {"sentiment": "positive", "confidence": 0.95}

    def test_parse_invalid_json_raises_error(self, parser):
        """Test error for invalid JSON."""
        response = "This is not JSON at all"

        with pytest.raises(ValueError) as exc_info:
            parser.parse_json_response(response)

        assert "No valid JSON found" in str(exc_info.value)

    def test_extract_sentiment_valid(self, parser):
        """Test sentiment extraction with valid response."""
        response = '{"sentiment": "positive", "confidence": 0.85}'
        result = parser.extract_sentiment(response)

        assert result['sentiment'] = 'positive'
        assert result['confidence'] = 0.85

    def test_extract_sentiment_invalid_value(self, parser):
        """Test error for invalid sentiment value."""
        response = '{"sentiment": "happy", "confidence": 0.85}'

        with pytest.raises(ValueError) as exc_info:
            parser.extract_sentiment(response)

        assert "Invalid sentiment" in str(exc_info.value)

    def test_extract_entities(self, parser):
        """Test entity extraction."""
        response = '{"entities": [{"name": "AWS", "type": "ORG"}]}'
        result = parser.extract_entities(response)

        assert len(result) = 1
        assert result[0]['name'] = 'AWS'