resource "aws_kms_key" "messaging" {
  description             = "${var.project} - SNS topic and SQS queues encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 7

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AccountAdministration"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${local.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowSnsToUseKeyForThisTopic"
        Effect    = "Allow"
        Principal = { Service = "sns.amazonaws.com" }
        Action    = ["kms:GenerateDataKey*", "kms:Decrypt"]
        Resource  = "*"
        Condition = {
          ArnEquals = { "aws:SourceArn" = local.topic_arn }
        }
      }
    ]
  })
}

resource "aws_kms_alias" "messaging" {
  name          = "alias/${var.project}-messaging"
  target_key_id = aws_kms_key.messaging.key_id
}