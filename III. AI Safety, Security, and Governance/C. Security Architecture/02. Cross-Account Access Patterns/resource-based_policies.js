{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::CONSUMER_ACCOUNT:root"},
    "Action": ["bedrock:InvokeModel"],
    "Resource": "arn:aws:bedrock:*:PROVIDER_ACCOUNT:custom-model/*"
  }]
}