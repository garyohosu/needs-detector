from needs_detector.infra.scanners.anonymizer import Anonymizer

def test_anonymizer_regex():
    text = "Contact me at test@example.com or 090-1234-5678. Zip is 123-4567. Website: http://example.com. IP: 192.168.1.1."
    res = Anonymizer.scan(text)
    assert "test@example.com" in res
    assert "090-1234-5678" in res
    assert "123-4567" in res
    assert "http://example.com." in res or "http://example.com" in res
    assert "192.168.1.1" in res
