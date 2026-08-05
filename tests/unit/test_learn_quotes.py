import pytest
import yaml
from needs_detector.core.services import LearnService
from needs_detector.domain.models.exceptions import QuoteValidationError

def test_quote_validation_error_line_bounds(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "interviews").mkdir()
    
    with open(project_dir / "project.yaml", "w", encoding="utf-8") as f:
        yaml.dump({"human_gate_enabled": False}, f)
        
    iv_file = project_dir / "interviews" / "interview_01.yaml"
    with open(iv_file, "w", encoding="utf-8") as f:
        # 3 lines
        yaml.dump({"content": "L1\nL2\nL3", "refutations": []}, f)
        
    # We will temporarily mock MockLLMProvider to return a bad line number
    from needs_detector.infra.llm.base import MockLLMProvider, LLMResponse
    original_generate = MockLLMProvider.generate
    
    def bad_generate(self, prompt_name, context, fixture_key=None, project_dir=None):
        import json
        return LLMResponse(
            content=json.dumps({
                "refutations": [
                    {"quote": "L1", "line": 4, "source": "src"}
                ]
            }),
            ai_completions=[],
            prompt_used=prompt_name,
            model_name="mock"
        )
        
    MockLLMProvider.generate = bad_generate
    try:
        with pytest.raises(QuoteValidationError, match="out of bounds"):
            LearnService.learn(project_dir, "mock")
    finally:
        MockLLMProvider.generate = original_generate

def test_quote_validation_error_not_substring(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "interviews").mkdir()
    
    with open(project_dir / "project.yaml", "w", encoding="utf-8") as f:
        yaml.dump({"human_gate_enabled": False}, f)
        
    iv_file = project_dir / "interviews" / "interview_01.yaml"
    with open(iv_file, "w", encoding="utf-8") as f:
        yaml.dump({"content": "L1\nL2\nL3", "refutations": []}, f)
        
    from needs_detector.infra.llm.base import MockLLMProvider, LLMResponse
    original_generate = MockLLMProvider.generate
    
    def bad_generate(self, prompt_name, context, fixture_key=None, project_dir=None):
        import json
        return LLMResponse(
            content=json.dumps({
                "refutations": [
                    {"quote": "I didn't use it", "line": 1, "source": "src"}
                ]
            }),
            ai_completions=[],
            prompt_used=prompt_name,
            model_name="mock"
        )
        
    MockLLMProvider.generate = bad_generate
    try:
        with pytest.raises(QuoteValidationError, match="not found in line"):
            LearnService.learn(project_dir, "mock")
    finally:
        MockLLMProvider.generate = original_generate
