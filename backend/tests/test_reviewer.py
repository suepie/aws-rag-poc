"""C3 の単体テスト: retrieval / postprocess / reviewer（Bedrock はフェイク）。"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from services import postprocess, reviewer  # noqa: E402
from services.excel_io import QARow  # noqa: E402
from services.providers.base import InvokeResult  # noqa: E402
from services.retrieval import get_strategy  # noqa: E402
from services.retrieval.base import RetrievalQuery  # noqa: E402

# --- retrieval ---------------------------------------------------------------

def test_fulltext_hits_encryption_reference():
    q = RetrievalQuery("Q1", "暗号化方式は？", "SSE-S3 (AES-256) を有効化", category="暗号化")
    items = get_strategy("fulltext").retrieve(q)
    assert items
    assert items[0].source_id == "ref-encryption"
    assert items[0].score > 0


def test_fulltext_no_hit_returns_empty():
    q = RetrievalQuery("Q1", "好きな色は？", "青")
    assert get_strategy("fulltext").retrieve(q) == []


def test_none_strategy_returns_empty():
    q = RetrievalQuery("Q1", "暗号化", "AES")
    assert get_strategy("none").retrieve(q) == []


def test_unknown_strategy_raises():
    with pytest.raises(ValueError):
        get_strategy("does-not-exist")


# --- postprocess -------------------------------------------------------------

def test_parse_plain_json():
    out = postprocess.parse_verdict('{"verdict":"approved","reply_draft":"OK","rationale":"r","confidence":"high"}')
    assert out["verdict"] == "approved"
    assert out["confidence"] == "high"


def test_parse_json_in_code_fence_with_prose():
    text = "判定します。\n```json\n{\"verdict\": \"conditional\", \"reply_draft\": \"x\", \"rationale\": \"y\", \"confidence\": \"medium\"}\n```\n以上。"
    out = postprocess.parse_verdict(text)
    assert out["verdict"] == "conditional"


def test_parse_invalid_verdict_falls_back():
    out = postprocess.parse_verdict('{"verdict":"maybe","confidence":"???"}')
    assert out["verdict"] == "needs_review"
    assert out["confidence"] == "medium"


def test_parse_no_json_raises():
    with pytest.raises(ValueError):
        postprocess.parse_verdict("ここに JSON はありません")


# --- reviewer orchestration --------------------------------------------------

class _FakeProvider:
    model_id = "fake"
    region = "ap-northeast-1"

    def __init__(self, text):
        self._text = text

    def invoke(self, spec):
        return InvokeResult(text=self._text)


def _row():
    return QARow(row_index=2, question_id="Q-003", category="データ保管",
                 question="保管リージョンは？", answer="ap-northeast-1 に保管し us-east-1 に複製")


def test_reviewer_returns_parsed_verdict_with_reference_titles():
    provider = _FakeProvider('{"verdict":"approved","reply_draft":"問題ありません","rationale":"複製あり","confidence":"high"}')
    rv = reviewer.Reviewer(provider=provider, strategy=get_strategy("fulltext"))
    v = rv.review(_row())
    assert v.verdict == "approved"
    assert v.reply_draft == "問題ありません"
    assert v.confidence == "high"
    assert any("リージョン" in t for t in v.reference_titles)  # fulltext がヒット


def test_reviewer_falls_back_on_bad_llm_output():
    provider = _FakeProvider("JSON ではない応答")
    rv = reviewer.Reviewer(provider=provider, strategy=get_strategy("none"))
    v = rv.review(_row())
    assert v.verdict == "needs_review"
    assert v.confidence == "low"


def test_reviewer_falls_back_on_provider_exception():
    class _Boom:
        def invoke(self, spec):
            raise RuntimeError("bedrock down")

    rv = reviewer.Reviewer(provider=_Boom(), strategy=get_strategy("none"))
    v = rv.review(_row())
    assert v.verdict == "needs_review"
    assert "失敗" in v.reply_draft
