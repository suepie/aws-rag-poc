"""Provider ファクトリ。"""
from __future__ import annotations

import os

from services.providers.base import Provider
from services.providers.claude_bedrock import ClaudeBedrockProvider

_REGISTRY = {
    "claude-sonnet-4-6": ClaudeBedrockProvider,
}


def get_provider(model_id: str | None = None) -> Provider:
    model_id = model_id or os.environ.get("DEFAULT_MODEL_ID", "claude-sonnet-4-6")
    factory = _REGISTRY.get(model_id)
    if factory is None:
        raise ValueError(f"unknown model_id: {model_id}")
    return factory()
