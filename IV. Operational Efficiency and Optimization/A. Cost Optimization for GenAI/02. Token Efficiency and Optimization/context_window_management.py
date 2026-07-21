# Instead of sending all 50 messages
# Send last 10 messages + summary of earlier context
context = summarize_history(messages[:40])
recent = messages[40:]
efficient_messages = [{"role": "system", "content": context}] + recent