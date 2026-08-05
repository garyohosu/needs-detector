from needs_detector.infra.scanners.anonymizer import Anonymizer


def test_anonymizer_regex():
    text = "Contact me at test@example.com or 090-1234-5678. Zip is 123-4567. Website: http://example.com. IP: 192.168.1.1."
    res = Anonymizer.scan(text)
    assert "test@example.com" in res
    assert "090-1234-5678" in res
    assert "123-4567" in res
    assert "http://example.com." in res or "http://example.com" in res
    assert "192.168.1.1" in res


def test_anonymizer_detects_legal_types_before_and_after_company_name():
    text = (
        "取引先はABC株式会社と株式会社サンプルです。"
        "青空有限会社と有限会社ミドリへ連絡した。"
        "ミライ合同会社と合同会社未来を確認した。"
    )

    res = Anonymizer.scan(text)

    assert "ABC株式会社" in res
    assert "株式会社サンプル" in res
    assert "青空有限会社" in res
    assert "有限会社ミドリ" in res
    assert "ミライ合同会社" in res
    assert "合同会社未来" in res


def test_anonymizer_supports_representative_company_name_characters():
    text = (
        "株式会社はてなへ連絡した。"
        "株式会社１２３を確認した。"
        "株式会社 日本へ連絡した。"
        "株式会社DMM.comを確認した。"
    )

    res = Anonymizer.scan(text)

    assert "株式会社はてな" in res
    assert "株式会社１２３" in res
    assert "株式会社 日本" in res
    assert "株式会社DMM.com" in res
    assert "株式会社DMM" not in res


def test_anonymizer_avoids_generic_context_and_branch_overmatch():
    assert Anonymizer.scan("一般的な株式会社制度を説明する。") == []
    assert Anonymizer.scan("顧客ABC株式会社へ連絡した。") == ["ABC株式会社"]
    assert Anonymizer.scan("今日はABC株式会社へ連絡した。") == ["ABC株式会社"]
    assert Anonymizer.scan("売却先のABC株式会社に確認した。") == ["ABC株式会社"]
    assert Anonymizer.scan("株式会社サンプル東京支店へ連絡した。") == [
        "株式会社サンプル"
    ]
    assert Anonymizer.scan("ABC株式会社担当者へ連絡した。") == ["ABC株式会社"]
    assert Anonymizer.scan("訪問した株式会社サンプルへ連絡した。") == [
        "株式会社サンプル"
    ]
    assert Anonymizer.scan("ABC株式会社とXYZ有限会社") == [
        "ABC株式会社",
        "XYZ有限会社",
    ]
    assert Anonymizer.scan("会社の課題も確認した。") == []
