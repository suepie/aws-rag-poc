"""Claude Sonnet 4.6 Provider（Amazon Bedrock Converse API）。

既定モデル: jp.anthropic.claude-sonnet-4-6（Cross-Region Inference Profile, 日本処理）。
プロンプト・出力は AWS 信頼境界内で完結（Anthropic には届かない）。
"""
from __future__ import annotations

import os
import time

import boto3

from services.providers.base import InvokeResult, PromptSpec


class ClaudeBedrockProvider:
    model_id = "claude-sonnet-4-6"

    def __init__(self):
        self.region = os.environ.get("CLAUDE_BEDROCK_REGION", "ap-northeast-1")
        self.bedrock_model_id = os.environ.get("CLAUDE_BEDROCK_MODEL_ID", "jp.anthropic.claude-sonnet-4-6")
        self.max_tokens = int(os.environ.get("CLAUDE_MAX_TOKENS", "1024"))
        self._client = None

    def _client_lazy(self):
        if self._client is None:
            self._client = boto3.client("bedrock-runtime", region_name=self.region)
        return self._client

    def invoke(self, spec: PromptSpec) -> InvokeResult:
        started = time.time()
        resp = self._client_lazy().converse(
            modelId=self.bedrock_model_id,
            system=[{"text": spec.system}],
            messages=[{"role": "user", "content": [{"text": spec.user}]}],
            inferenceConfig={"temperature": 0.0, "maxTokens": self.max_tokens},
        )
        latency_ms = int((time.time() - started) * 1000)
        text = resp["output"]["message"]["content"][0]["text"]
        usage = resp.get("usage", {})
        return InvokeResult(
            text=text,
            input_tokens=usage.get("inputTokens", 0),
            output_tokens=usage.get("outputTokens", 0),
            latency_ms=latency_ms,
        )
