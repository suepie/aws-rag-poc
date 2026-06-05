data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name = "${var.project}-${var.env}"
  azs  = slice(data.aws_availability_zones.available.names, 0, length(var.private_subnet_cidrs))
}

# ネットワーク（VPC + プライベートサブネット）。Aurora 専用（Phase 2）。
# Lambda は API / Worker とも VPC 外（ADR-007）。ここに Lambda はアタッチしない。
module "network" {
  source               = "./modules/network"
  name                 = local.name
  vpc_cidr             = var.vpc_cidr
  private_subnet_cidrs = var.private_subnet_cidrs
  azs                  = local.azs
}

module "s3" {
  source = "./modules/s3"
  name   = local.name
}

module "dynamodb" {
  source = "./modules/dynamodb"
  name   = local.name
}

module "lambda" {
  source           = "./modules/lambda"
  name             = local.name
  zip_path         = var.lambda_zip_path
  jobs_table_name  = module.dynamodb.table_name
  jobs_table_arn   = module.dynamodb.table_arn
  excel_bucket     = module.s3.bucket_name
  excel_bucket_arn = module.s3.bucket_arn
  api_memory       = var.api_memory
  api_timeout      = var.api_timeout
  worker_memory    = var.worker_memory
  worker_timeout   = var.worker_timeout
  presign_expires  = var.presign_expires
  job_ttl_days     = var.job_ttl_days
}

module "apigw_rest" {
  source          = "./modules/apigw-rest"
  name            = local.name
  region          = var.region
  api_lambda_arn  = module.lambda.api_invoke_arn
  api_lambda_name = module.lambda.api_function_name
}
