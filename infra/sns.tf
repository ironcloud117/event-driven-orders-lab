resource "aws_sns_topic" "orders" {
  name              = local.topic_name
  kms_master_key_id = aws_kms_key.messaging.arn
}

resource "aws_sns_topic_subscription" "consumers" {
  for_each = local.consumers

  topic_arn            = aws_sns_topic.orders.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.main[each.key].arn
  raw_message_delivery = true

  depends_on = [aws_sqs_queue_policy.main]
}