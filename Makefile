.PHONY: tf-init tf-plan tf-apply tf-destroy tf-output \
       tf-url tf-api-url tf-sn-api-url tf-api-key tf-invalidate-cache \
       deploy-backend deploy-frontend deploy-all build-lambda aurora-init bedrock-kb-init \
       be-lint be-test \
       fe-dev fe-lint fe-type-check fe-build fe-env \
       cognito-create-user cognito-list-users \
       logs-api logs-worker logs-authorizer logs-apigw \
       sn-test seed-references \
       help

# ==============================================================================
# 設定
# ==============================================================================

TF_DIR        := infra/terraform
TF_VARS_FILE  := environments/dev/terraform.tfvars
FRONTEND_SRC  := frontend
FRONTEND_DIST := frontend/dist
BACKEND_SRC   := backend
BEDROCK_REGION := ap-northeast-1

# ==============================================================================
# [tf-*] Terraform 基本操作
# ==============================================================================

tf-init: ## [terraform] 初期化
	cd $(TF_DIR) && terraform init

tf-plan: ## [terraform] 変更確認
	cd $(TF_DIR) && terraform plan -var-file=$(TF_VARS_FILE)

tf-apply: ## [terraform] インフラ構築・更新
	cd $(TF_DIR) && terraform apply -var-file=$(TF_VARS_FILE)

tf-destroy: ## [terraform] 全リソース削除
	cd $(TF_DIR) && terraform destroy -var-file=$(TF_VARS_FILE)

tf-output: ## [terraform] output 表示
	cd $(TF_DIR) && terraform output

# ==============================================================================
# [tf-*] Terraform ユーティリティ
# ==============================================================================

tf-url: ## [terraform] CloudFront URL（SPA）を表示
	@cd $(TF_DIR) && echo "https://$$(terraform output -raw cloudfront_distribution_domain)"

tf-api-url: ## [terraform] SPA 用 HTTP API の URL を表示
	@cd $(TF_DIR) && terraform output -raw api_endpoint

tf-sn-api-url: ## [terraform] ServiceNow 用 REST API（/v1）の URL を表示
	@cd $(TF_DIR) && terraform output -raw servicenow_api_endpoint

tf-api-key: ## [terraform] ServiceNow 用 APIキーの値を取得（取扱注意）
	$(eval KEY_ID := $(shell cd $(TF_DIR) && terraform output -raw servicenow_api_key_id))
	@aws apigateway get-api-key --api-key $(KEY_ID) --include-value \
		--query value --output text --no-cli-pager

tf-invalidate-cache: ## [terraform] CloudFront キャッシュ無効化
	$(eval DIST_ID := $(shell cd $(TF_DIR) && terraform output -raw cloudfront_distribution_id))
	aws cloudfront create-invalidation --distribution-id $(DIST_ID) --paths "/*" --no-cli-pager

# ==============================================================================
# [deploy-*] デプロイ
# ==============================================================================

build-lambda: ## [deploy] Lambda パッケージをビルド（pip 依存: pymysql, openpyxl 等）
	bash scripts/build-lambda.sh

deploy-backend: build-lambda ## [deploy] Lambda + API GW のみ（バックエンド変更時）
	cd $(TF_DIR) && terraform apply -var-file=$(TF_VARS_FILE) \
		-target=module.lambda -target=module.apigw-rest -target=module.apigw-http

aurora-init: ## [aurora] スキーマ作成 + 初期データ移行
	bash scripts/aurora-init.sh

bedrock-kb-init: ## [bedrock-kb] Knowledge Base / OpenSearch Serverless を CLI で先行作成（bedrock_kb 戦略採用時のみ）
	bash scripts/bedrock-kb-init.sh

deploy-frontend: fe-build ## [deploy] フロントエンド（ビルド + S3 + キャッシュ無効化）
	$(eval BUCKET := $(shell cd $(TF_DIR) && terraform output -raw s3_bucket_name))
	$(eval DIST_ID := $(shell cd $(TF_DIR) && terraform output -raw cloudfront_distribution_id))
	aws s3 sync $(FRONTEND_DIST)/ s3://$(BUCKET) --delete
	aws cloudfront create-invalidation --distribution-id $(DIST_ID) --paths "/*" --no-cli-pager
	@echo "フロントエンドのデプロイ完了: $(BUCKET)"

deploy-all: tf-apply deploy-frontend ## [deploy] 全て（terraform apply → ビルド → S3 → キャッシュ無効化）

# ==============================================================================
# [be-*] バックエンド開発
# ==============================================================================

be-lint: ## [backend] ruff lint
	cd $(BACKEND_SRC) && ruff check src/

be-test: ## [backend] pytest
	cd $(BACKEND_SRC) && python -m pytest tests/ -v

# ==============================================================================
# [fe-*] フロントエンド開発
# ==============================================================================

fe-dev: ## [frontend] 開発サーバー起動（モック認証可）
	cd $(FRONTEND_SRC) && npx vite

fe-lint: ## [frontend] ESLint
	cd $(FRONTEND_SRC) && npx eslint src/

fe-type-check: ## [frontend] TypeScript 型チェック
	cd $(FRONTEND_SRC) && npx tsc --noEmit

fe-build: ## [frontend] ビルド
	cd $(FRONTEND_SRC) && npx vite build

fe-env: ## [frontend] .env を terraform output から自動生成
	@cd $(TF_DIR) && echo "VITE_USE_MOCK=false" > ../../$(FRONTEND_SRC)/.env
	@cd $(TF_DIR) && echo "VITE_MOCK_AUTH=false" >> ../../$(FRONTEND_SRC)/.env
	@cd $(TF_DIR) && echo "VITE_COGNITO_USER_POOL_ID=$$(terraform output -raw cognito_user_pool_id)" >> ../../$(FRONTEND_SRC)/.env
	@cd $(TF_DIR) && echo "VITE_COGNITO_CLIENT_ID=$$(terraform output -raw cognito_client_id)" >> ../../$(FRONTEND_SRC)/.env
	@cd $(TF_DIR) && echo "VITE_API_BASE_URL=$$(terraform output -raw api_endpoint)" >> ../../$(FRONTEND_SRC)/.env
	@echo ".env 生成完了:" && cat $(FRONTEND_SRC)/.env

# ==============================================================================
# [cognito-*] Cognito ユーザー管理（SPA 用）
# ==============================================================================

COGNITO_EMAIL ?= dev@example.com
COGNITO_PASSWORD ?= DevPass123

cognito-create-user: ## [cognito] ユーザー作成（COGNITO_EMAIL/COGNITO_PASSWORD 指定可）
	$(eval POOL_ID := $(shell cd $(TF_DIR) && terraform output -raw cognito_user_pool_id))
	aws cognito-idp admin-create-user --user-pool-id $(POOL_ID) --username $(COGNITO_EMAIL) \
		--user-attributes Name=email,Value=$(COGNITO_EMAIL) Name=email_verified,Value=true \
		--message-action SUPPRESS --no-cli-pager
	aws cognito-idp admin-set-user-password --user-pool-id $(POOL_ID) --username $(COGNITO_EMAIL) \
		--password $(COGNITO_PASSWORD) --permanent --no-cli-pager
	@echo "ユーザー作成完了: $(COGNITO_EMAIL)"

cognito-list-users: ## [cognito] ユーザー一覧
	$(eval POOL_ID := $(shell cd $(TF_DIR) && terraform output -raw cognito_user_pool_id))
	aws cognito-idp list-users --user-pool-id $(POOL_ID) --no-cli-pager

# ==============================================================================
# [logs-*] ログ確認
# ==============================================================================

LOG_SINCE ?= 30m

logs-api: ## [logs] Lambda API のログ（LOG_SINCE=30m で期間指定）
	$(eval FUNC := $(shell cd $(TF_DIR) && terraform output -raw lambda_function_name))
	aws logs tail /aws/lambda/$(FUNC) --since $(LOG_SINCE) --follow --no-cli-pager

logs-worker: ## [logs] Lambda Worker のログ
	$(eval FUNC := $(shell cd $(TF_DIR) && terraform output -raw worker_function_name))
	aws logs tail /aws/lambda/$(FUNC) --since $(LOG_SINCE) --follow --no-cli-pager

logs-authorizer: ## [logs] Lambda Authorizer のログ
	$(eval PROJECT := $(shell cd $(TF_DIR) && terraform output -raw lambda_function_name | sed 's/-api-/-authorizer-/'))
	aws logs tail /aws/lambda/$(PROJECT) --since $(LOG_SINCE) --follow --no-cli-pager

logs-apigw: ## [logs] API Gateway アクセスログ
	aws logs tail /aws/apigateway/aws-rag-poc-dev --since $(LOG_SINCE) --follow --no-cli-pager

# ==============================================================================
# [sn-*] ServiceNow 連携テスト
# ==============================================================================

sn-test: ## [servicenow] /v1/uploads を APIキー付きで叩いて疎通確認（API_KEY=xxx）
	$(eval API_URL := $(shell cd $(TF_DIR) && terraform output -raw servicenow_api_endpoint))
	@if [ -z "$(API_KEY)" ]; then echo "使い方: make sn-test API_KEY=\$$(make -s tf-api-key)"; exit 1; fi
	@echo "=== POST $(API_URL)/v1/uploads ==="
	@curl -s -X POST "$(API_URL)/v1/uploads" \
		-H "Content-Type: application/json" \
		-H "x-api-key: $(API_KEY)" \
		-d '{"filename":"test.xlsx","content_type":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}' \
		| python3 -m json.tool

# ==============================================================================
# [seed-*] 初期データ
# ==============================================================================

seed-references: ## [seed] 参考情報マスタの初期データを投入
	bash scripts/seed-references.sh

# ==============================================================================
# ヘルプ
# ==============================================================================

help: ## このヘルプを表示
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
