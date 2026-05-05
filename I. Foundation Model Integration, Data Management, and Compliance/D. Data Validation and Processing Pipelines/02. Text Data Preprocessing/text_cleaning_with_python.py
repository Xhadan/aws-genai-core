import re
import unicodedata
from html import unescape

def clean_text(text):
    """Clean raw text for GenAI processing."""
    # Decode HTML entities
    text = unescape(text)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Fix Unicode issues
    text = unicodedata.normalize('NFC', text)

    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '[URL]', text)

    # Remove email addresses
    text = re.sub(r'\S+@\S+\.\S+', '[EMAIL]', text)

    # Standardize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove control characters (keep newlines)
    text = ''.join(char for char in text if unicodedata.category(char) != 'Cc' or char in '\n\t')

    return text.strip()

# Example usage
raw_text = """
<html><p>Contact us at support@company.com or visit https://example.com</p></html>
Multiple   spaces   and   tabs		here.
"""
clean = clean_text(raw_text)
# Output: "Contact us at [EMAIL] or visit [URL] Multiple spaces and tabs here."