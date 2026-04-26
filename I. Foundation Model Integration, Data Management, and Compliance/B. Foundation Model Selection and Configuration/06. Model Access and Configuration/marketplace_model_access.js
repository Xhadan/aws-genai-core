{
  "Effect": "Allow",
  "Action": "aws-marketplace:Subscribe",
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "aws-marketplace:ProductId": "specific-product-id"
    }
  }
}