"""PII フィルタの単体テスト。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from services import pii_filter  # noqa: E402


def test_redacts_email_and_ip():
    out = pii_filter.redact_text("連絡先は taro@example.com、IP は 10.0.0.1 です")
    assert "taro@example.com" not in out
    assert "10.0.0.1" not in out
    assert "[REDACTED]" in out


def test_redacts_aws_key_and_mynumber():
    out = pii_filter.redact_text("key=AKIAIOSFODNN7EXAMPLE no=123456789012")
    assert "AKIAIOSFODNN7EXAMPLE" not in out
    assert "123456789012" not in out


def test_keeps_normal_text():
    assert pii_filter.redact_text("ap-northeast-1 に保管") == "ap-northeast-1 に保管"
