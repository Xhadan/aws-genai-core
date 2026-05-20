from collections import Counter

def majority_vote(answers):
    """Simple majority voting."""
    counter = Counter(answers)
    winner, count = counter.most_common(1)[0]
    confidence = count / len(answers)
    return winner, confidence

answers = ["42", "42", "38", "42", "42"]
result, conf = majority_vote(answers)
# result: "42", conf: 0.8