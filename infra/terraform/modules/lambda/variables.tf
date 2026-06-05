variable "name" { type = string }
variable "zip_path" { type = string }
variable "jobs_table_name" { type = string }
variable "jobs_table_arn" { type = string }
variable "excel_bucket" { type = string }
variable "excel_bucket_arn" { type = string }
variable "api_memory" { type = number }
variable "api_timeout" { type = number }
variable "worker_memory" { type = number }
variable "worker_timeout" { type = number }
variable "presign_expires" { type = number }
variable "job_ttl_days" { type = number }

variable "default_model_id" {
  type    = string
  default = "claude-sonnet-4-6"
}
variable "default_retrieval_strategy_id" {
  type    = string
  default = "fulltext"
}
variable "claude_bedrock_region" {
  type    = string
  default = "ap-northeast-1"
}
variable "claude_bedrock_model_id" {
  type    = string
  default = "jp.anthropic.claude-sonnet-4-6"
}
