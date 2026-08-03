# Run multiple evaluations, take majority
scores = [evaluate(response) for _ in range(3)]
final_score = statistics.mode(scores)