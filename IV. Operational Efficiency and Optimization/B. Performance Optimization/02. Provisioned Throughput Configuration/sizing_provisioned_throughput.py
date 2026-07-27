# Analyze CloudWatch metrics
peak_input_tokens = 200000  # per minute
peak_output_tokens = 300000  # per minute
total_peak = peak_input_tokens + peak_output_tokens

mu_capacity = 100000  # tokens/min per MU for Sonnet
required_mus = (total_peak * 1.3) / mu_capacity  # 30% buffer
# Result: 6.5 -> round up to 7 MUs