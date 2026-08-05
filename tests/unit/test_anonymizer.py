import pytest
from needs_detector.infra.scanners.anonymizer import Anonymizer

def test_anonymizer_detection():
    text = "山田太郎 (yamada@example.com, 090-1234-5678, ABC株式会社) にインタビューを実施した。"
    res = Anonymizer.scan(text)
    assert "山田太郎" in res
    assert "yamada@example.com" in res
    assert "090-1234-5678" in res
    assert "ABC株式会社" in res
