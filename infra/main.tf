data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.region

  topic_name = "${var.project}-orders"
  topic_arn  = "arn:aws:sns:${local.region}:${local.account_id}:${local.topic_name}"
}