variable "project" {
  type    = string
  default = "aws-rag-poc"
}

variable "env" {
  type    = string
  default = "dev"
}

variable "region" {
  type    = string
  default = "ap-northeast-1"
}

# --- network ---
variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.16.0/20", "10.0.32.0/20"]
}

# --- lambda ---
variable "lambda_zip_path" {
  type        = string
  default     = "../../backend/dist/lambda.zip"
  description = "make build-lambda で生成する Lambda パッケージ"
}

variable "api_memory" {
  type    = number
  default = 512
}

variable "api_timeout" {
  type    = number
  default = 30
}

variable "worker_memory" {
  type    = number
  default = 512
}

variable "worker_timeout" {
  type    = number
  default = 300
}

variable "presign_expires" {
  type    = number
  default = 900
}

variable "job_ttl_days" {
  type    = number
  default = 7
}
