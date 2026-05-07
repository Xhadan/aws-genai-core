# Data Wrangler Custom Transform
import pandas as pd
import re

def clean_text(df):
    """Custom text cleaning for fine-tuning data."""

    def clean_field(text):
        if pd.isna(text):
            return ""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', str(text))
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char = '\n')
        return text.strip()

    df['prompt_clean'] = df['prompt'].apply(clean_field)
    df['completion_clean'] = df['completion'].apply(clean_field)

    return df

# Apply transform
df = clean_text(df)