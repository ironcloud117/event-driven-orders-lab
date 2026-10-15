variable "region" {
  description = "AWS region for all lab resources"
  type        = string
  default     = "eu-west-1"
}

variable "project" {
  description = "Project name, used as prefix for resource names and as cost tag"
  type        = string
  default     = "edo-lab"
}

variable "max_receive_count" {
  description = "Delivery attempts before a message is moved to the DLQ"
  type        = number
  default     = 3
}