output "invoke_url" {
  value = aws_api_gateway_stage.this.invoke_url
}

output "api_key_id" {
  value = aws_api_gateway_api_key.servicenow.id
}

output "rest_api_id" {
  value = aws_api_gateway_rest_api.this.id
}
