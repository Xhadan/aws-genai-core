# CloudWatch alarm for high utilization
alarm_threshold = 80  # percent utilization
if current_utilization > alarm_threshold:
    increase_model_units()