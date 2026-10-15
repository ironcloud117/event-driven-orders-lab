data "archive_file" "consumer" {
  for_each = local.consumers

  type        = "zip"
  source_file = "${path.module}/../src/${each.key}/handler.py"
  output_path = "${path.module}/build/${each.key}.zip"
}

resource "aws_cloudwatch_log_group" "consumer" {
  for_each = local.consumers

  name              = "/aws/lambda/${var.project}-${each.key}"
  retention_in_days = 7
}

resource "aws_lambda_function" "consumer" {
  for_each = local.consumers

  function_name    = "${var.project}-${each.key}"
  role             = aws_iam_role.consumer[each.key].arn
  runtime          = "python3.13"
  architectures    = ["arm64"]
  handler          = "handler.handler"
  filename         = data.archive_file.consumer[each.key].output_path
  source_code_hash = data.archive_file.consumer[each.key].output_base64sha256
  memory_size      = 128
  timeout          = 10

  environment {
    variables = {
      SIMULATE_FAILURE = "false"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.consumer,
    aws_iam_role_policy.consumer
  ]
}

resource "aws_lambda_event_source_mapping" "consumer" {
  for_each = local.consumers

  event_source_arn                   = aws_sqs_queue.main[each.key].arn
  function_name                      = aws_lambda_function.consumer[each.key].arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
  function_response_types            = ["ReportBatchItemFailures"]
  enabled                            = true

  scaling_config {
    maximum_concurrency = 2
  }
}