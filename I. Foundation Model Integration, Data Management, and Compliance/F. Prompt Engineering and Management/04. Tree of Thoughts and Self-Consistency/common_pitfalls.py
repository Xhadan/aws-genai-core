# Instruct consistent format in prompt
prompt = """
...solve the problem...
End your response with exactly:
FINAL ANSWER: [number]
"""

# Use strict regex for extraction
match = re.search(r'FINAL ANSWER:\s*(.+?)$', response, re.MULTILINE)