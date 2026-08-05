import pytest
from pydantic import ValidationError
from needs_detector.infra.llm.base import MockLLMProvider

def test_pydantic_validation_error_invalid_json():
    # If JSON is invalid, standard json library will raise JSONDecodeError
    import json
    
    class BadMockLLMProvider(MockLLMProvider):
        def _get_fixture_key(self, context: str) -> str:
            return "invalid_json"
            
    # We will write an invalid JSON file to the fixtures dir temporarily
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as d:
        provider = BadMockLLMProvider()
        provider.fixtures_dir = Path(d)
        
        invalid_path = provider.fixtures_dir / "invalid_json_draw_persona.json"
        invalid_path.write_text("{ bad json ", encoding="utf-8")
        
        with pytest.raises(json.JSONDecodeError):
            provider.generate("draw_persona", "context")

def test_pydantic_validation_error_schema():
    # Write a valid JSON but invalid schema (missing required fields)
    class BadSchemaProvider(MockLLMProvider):
        def _get_fixture_key(self, context: str) -> str:
            return "bad_schema"
            
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as d:
        provider = BadSchemaProvider()
        provider.fixtures_dir = Path(d)
        
        invalid_path = provider.fixtures_dir / "bad_schema_draw_persona.json"
        # Missing 'personas' list
        invalid_path.write_text('{"other": 1}', encoding="utf-8")
        
        with pytest.raises(ValidationError):
            provider.generate("draw_persona", "context")
            
def test_pydantic_validation_error_evidence_type():
    # Invalid evidence type
    class BadEvidenceProvider(MockLLMProvider):
        def _get_fixture_key(self, context: str) -> str:
            return "bad_evidence"
            
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as d:
        provider = BadEvidenceProvider()
        provider.fixtures_dir = Path(d)
        
        invalid_path = provider.fixtures_dir / "bad_evidence_learn_refutations.json"
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
        
        with pytest.raises(ValidationError):
            provider.generate("learn_refutations", "context")
