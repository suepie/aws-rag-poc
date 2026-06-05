# Excel 入出力バケット（presigned PUT/GET 用）。POC のため force_destroy。
resource "aws_s3_bucket" "excel" {
  bucket        = "${var.name}-excel"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "excel" {
  bucket                  = aws_s3_bucket.excel.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "excel" {
  bucket = aws_s3_bucket.excel.id
  rule {
    id     = "expire-inbound-outbound"
    status = "Enabled"
    filter { prefix = "reviews/" }
    expiration { days = 30 }
  }
}

# presigned PUT を許可するため CORS（ServiceNow は直接 PUT する）
resource "aws_s3_bucket_cors_configuration" "excel" {
  bucket = aws_s3_bucket.excel.id
  cors_rule {
    allowed_methods = ["PUT", "GET"]
    allowed_origins = ["*"]
    allowed_headers = ["*"]
    max_age_seconds = 3000
  }
}
