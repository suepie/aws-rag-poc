output "servicenow_api_endpoint" {
  description = "ServiceNow 用 REST API（/v1）のベース URL"
  value       = module.apigw_rest.invoke_url
}

output "servicenow_api_key_id" {
  description = "ServiceNow 用 APIキーの ID（値は make tf-api-key で取得）"
  value       = module.apigw_rest.api_key_id
}

output "excel_bucket_name" {
  value = module.s3.bucket_name
}

output "jobs_table_name" {
  value = module.dynamodb.table_name
}

output "lambda_function_name" {
  value = module.lambda.api_function_name
}

output "worker_function_name" {
  value = module.lambda.worker_function_name
}

output "vpc_id" {
  value = module.network.vpc_id
}
