data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ---------------------------------------------------------------------------
# 共有: ログ出力の基本ポリシー
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# ---------------------------------------------------------------------------
# API Lambda
# ---------------------------------------------------------------------------
resource "aws_iam_role" "api" {
  name               = "${var.name}-api-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

data "aws_iam_policy_document" "api" {
  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
  statement {
    sid       = "Jobs"
    actions   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem"]
    resources = [var.jobs_table_arn]
  }
  statement {
    sid       = "Excel"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${var.excel_bucket_arn}/*"]
  }
  statement {
    sid       = "InvokeWorker"
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.worker.arn]
  }
}

resource "aws_iam_role_policy" "api" {
  role   = aws_iam_role.api.id
  policy = data.aws_iam_policy_document.api.json
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/${var.name}-api"
  retention_in_days = 7
}

resource "aws_lambda_function" "api" {
  function_name    = "${var.name}-api"
  role             = aws_iam_role.api.arn
  runtime          = "python3.12"
  handler          = "handlers.api.lambda_handler"
  filename         = var.zip_path
  source_code_hash = filebase64sha256(var.zip_path)
  memory_size      = var.api_memory
  timeout          = var.api_timeout
  depends_on       = [aws_cloudwatch_log_group.api]

  environment {
    variables = {
      JOBS_TABLE           = var.jobs_table_name
      EXCEL_BUCKET         = var.excel_bucket
      WORKER_FUNCTION_NAME = aws_lambda_function.worker.function_name
      PRESIGN_EXPIRES      = tostring(var.presign_expires)
      JOB_TTL_DAYS         = tostring(var.job_ttl_days)
    }
  }
}

# ---------------------------------------------------------------------------
# Worker Lambda
# ---------------------------------------------------------------------------
resource "aws_iam_role" "worker" {
  name               = "${var.name}-worker-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

data "aws_iam_policy_document" "worker" {
  statement {
    sid       = "Logs"
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
  statement {
    sid       = "Jobs"
    actions   = ["dynamodb:GetItem", "dynamodb:UpdateItem"]
    resources = [var.jobs_table_arn]
  }
  statement {
    sid       = "Excel"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${var.excel_bucket_arn}/*"]
  }
  statement {
    sid       = "Bedrock"
    actions   = ["bedrock:InvokeModel", "bedrock:Converse"]
    resources = ["*"] # POC。本番では Claude モデル + Inference Profile の ARN に限定する。
  }
}

resource "aws_iam_role_policy" "worker" {
  role   = aws_iam_role.worker.id
  policy = data.aws_iam_policy_document.worker.json
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/aws/lambda/${var.name}-worker"
  retention_in_days = 7
}

resource "aws_lambda_function" "worker" {
  function_name    = "${var.name}-worker"
  role             = aws_iam_role.worker.arn
  runtime          = "python3.12"
  handler          = "handlers.worker.lambda_handler"
  filename         = var.zip_path
  source_code_hash = filebase64sha256(var.zip_path)
  memory_size      = var.worker_memory
  timeout          = var.worker_timeout
  depends_on       = [aws_cloudwatch_log_group.worker]

  environment {
    variables = {
      JOBS_TABLE                    = var.jobs_table_name
      EXCEL_BUCKET                  = var.excel_bucket
      JOB_TTL_DAYS                  = tostring(var.job_ttl_days)
      DEFAULT_MODEL_ID              = var.default_model_id
      DEFAULT_RETRIEVAL_STRATEGY_ID = var.default_retrieval_strategy_id
      CLAUDE_BEDROCK_REGION         = var.claude_bedrock_region
      CLAUDE_BEDROCK_MODEL_ID       = var.claude_bedrock_model_id
    }
  }
}
