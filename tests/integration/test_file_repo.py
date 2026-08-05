import pytest
from pathlib import Path
from needs_detector.infra.repositories.file_utils import atomic_write

def test_atomic_write(tmp_path):
    p = tmp_path / "test.txt"
    atomic_write(p, "hello")
    assert p.read_text(encoding="utf-8") == "hello"
