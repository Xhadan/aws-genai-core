for question in test_questions:
    response_a = generate(prompt_template_a, question)
    response_b = generate(prompt_template_b, question)
    result = pairwise_compare(question, response_a, response_b)
    results.append(result)

win_rate_a = sum(1 for r in results if r['winner'] = 'A') / len(results)