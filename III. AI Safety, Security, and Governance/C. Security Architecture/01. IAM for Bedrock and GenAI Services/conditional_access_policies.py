import json

# Restrict to specific models using conditions
model_restricted_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowSpecificModels",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:Converse"
            ],
            "Resource": "*",
            "Condition": {
                "StringLike": {
                    "bedrock:ModelId": [
                        "anthropic.claude-3-haiku*",
                        "amazon.titan-text-lite*"
                    ]
                }
            }
        }
    ]
}

# Require guardrail for all invocations
guardrail_required_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyWithoutGuardrail",
            "Effect": "Deny",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:Converse"
            ],
            "Resource": "*",
            "Condition": {
                "Null": {
                    "bedrock:GuardrailIdentifier": "true"
                }
            }
        },
        {
            "Sid": "AllowWithGuardrail",
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:Converse"
            ],
            "Resource": "*"
        }
    ]
}

# Time-based access (business hours only)
time_restricted_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "BusinessHoursOnly",
            "Effect": "Allow",
            "Action": "bedrock:*",
            "Resource": "*",
            "Condition": {
                "DateGreaterThan": {"aws:CurrentTime": "2024-01-01T09:00:00Z"},
                "DateLessThan": {"aws:CurrentTime": "2024-12-31T17:00:00Z"}
            }
        }
    ]
}

# IP-based restrictions
ip_restricted_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowFromCorporateNetwork",
            "Effect": "Allow",
            "Action": "bedrock:*",
            "Resource": "*",
            "Condition": {
                "IpAddress": {
                    "aws:SourceIp": [
                        "203.0.113.0/24",
                        "198.51.100.0/24"
                    ]
                }
            }
        }
    ]
}