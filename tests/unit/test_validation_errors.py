import pytest
import os
import json
from pydantic import ValidationError
from needs_detector.infra.llm.base import MockLLMProvider
from pathlib import Path

def test_pydantic_validation_error_invalid_json():
    class BadMockLLMProvider(MockLLMProvider):
        def _get_fixture_key(self, context: str, fixture_key: str = None, project_dir=None) -> str:
            return "invalid_json"

    provider = BadMockLLMProvider()
    invalid_path = Path("src/needs_detector/fixtures/llm/invalid_json_draw_persona.json")
    invalid_path.write_text("{ bad json ", encoding="utf-8")
    
    try:
        with pytest.raises(json.JSONDecodeError):
            provider.generate("draw_persona", "context")
    finally:
        invalid_path.unlink()

def test_pydantic_validation_error_schema():
    class BadSchemaProvider(MockLLMProvider):
        def _get_fixture_key(self, context: str, fixture_key: str = None, project_dir=None) -> str:
            return "bad_schema"

    provider = BadSchemaProvider()
    invalid_path = Path("src/needs_detector/fixtures/llm/bad_schema_draw_persona.json")
    invalid_path.write_text('{"other": 1}', encoding="utf-8")
    
    try:
        with pytest.raises(ValidationError):
            provider.generate("draw_persona", "context")
    finally:
        invalid_path.unlink()

def test_pydantic_validation_error_evidence_type():
    class BadEvidenceProvider(MockLLMProvider):
        def _get_fixture_key(self, context: str, fixture_key: str = None, project_dir=None) -> str:
            return "bad_evidence"

    provider = BadEvidenceProvider()
    invalid_path = Path("src/needs_detector/fixtures/llm/bad_evidence_learn_refutations.json")
    invalid_path.write_text('''
    {
        "refutations": [
            {
                "quote": "abc",
                "line": 1,
                "source": "src",
                "evidence": {
                    "evidence_type": "magical_type",
                    "content": "xyz"
                }
            }
        ]
    }
    ''', encoding="utf-8")
    
    try:
        with pytest.raises(ValidationError):
            provider.generate("learn_refutations", "context")
    finally:
        invalid_path.unlink()
