# Check what was retrieved
for chunk in retrieved_chunks:
    print(f"Score: {chunk.score}, Content: {chunk.text[:100]}")