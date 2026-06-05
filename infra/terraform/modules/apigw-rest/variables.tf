variable "name" { type = string }
variable "region" { type = string }
variable "api_lambda_arn" {
  type        = string
  description = "API Lambda の invoke_arn"
}
variable "api_lambda_name" { type = string }
variable "stage_name" {
  type    = string
  default = "prod"
}
variable "throttle_rate" {
  type    = number
  default = 10
}
variable "throttle_burst" {
  type    = number
  default = 20
}
