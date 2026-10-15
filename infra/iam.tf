resource "aws_iam_role" "consumer" {
  for_each = local.consumers

  name = "${var.project}-${each.key}-consumer"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
        Action    = "sts:AssumeRole"
        Condition = {
          StringEquals = { "aws:SourceAccount" = local.account_id }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "consumer" {
  for_each = local.consumers

  name = "${var.project}-${each.key}-consumer"
  role = aws_iam_role.consumer[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ConsumeOwnQueueOnly"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:ChangeMessageVisibility",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.main[each.key].arn
      },
      {
        Sid      = "DecryptViaSqsOnly"
        Effect   = "Allow"
        Action   = "kms:Decrypt"
        Resource = aws_kms_key.messaging.arn
        Condition = {
          StringEquals = { "kms:ViaService" = "sqs.${local.region}.amazonaws.com" }
        }
      },
      {
        Sid    = "WriteOwnLogsOnly"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${local.region}:${local.account_id}:log-group:/aws/lambda/${var.project}-${each.key}:*"
      }
    ]
  })
}