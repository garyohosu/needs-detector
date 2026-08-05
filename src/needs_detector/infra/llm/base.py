import json
import os
import re
from pathlib import Path
from abc import ABC, abstractmethod
from needs_detector.domain.models.llm_models import (
    DrawResponse, ExploreResponse, InterviewGuideResponse, InterviewAnalysisResponse
)

class LLMResponse:
    def __init__(self, content, ai_completions, prompt_used, model_name):
        self.content = content
        self.ai_completions = ai_completions
        self.prompt_used = prompt_used
        self.model_name = model_name

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt_name, context):
        pass

class MockLLMProvider(LLMProvider):
    def __init__(self):
        self.fixtures_dir = Path(os.getcwd()) / "tests" / "fixtures" / "llm"

    def _get_fixture_key(self, context: str) -> str:
        # Check context for fixture key
        match = re.search(r'FIXTURE_KEY:\s*([\w\-]+)', str(context))
        if match:
            return match.group(1)
            
        if "Persona A" in str(context):
            return "dataset_a"
        if "Persona B" in str(context):
            return "dataset_b"
            
        # Check env
        env_key = os.environ.get('MOCK_FIXTURE_KEY')
        if env_key:
            return env_key
        return "default"

    def generate(self, prompt_name, context):
        fixture_key = self._get_fixture_key(context)
        fixture_path = self.fixtures_dir / f"{fixture_key}_{prompt_name}.json"
        
        if not fixture_path.exists():
            # Fallback to default if not found
            fixture_path = self.fixtures_dir / f"default_{prompt_name}.json"
        
        if fixture_path.exists():
            content = fixture_path.read_text(encoding='utf-8')
        else:
            # Provide hardcoded fallback for tests if fixture doesn't exist yet
            if prompt_name == 'draw_persona':
                content = json.dumps({"personas": [{"id": "p1", "name": "Persona 1", "situation": "Busy", "jobs": {"functional": "F", "emotional": "E", "social": "S"}, "impediments": "I", "current_coping": "C", "dissatisfaction": "D", "evidence_type": "evidence", "source_reference": "ref", "questions_to_verify": ["Q1"]}]})
            elif prompt_name == 'explore_alternatives':
                content = json.dumps({"direct_competition": [], "indirect_alternatives": [], "non_consumption": []})
            elif prompt_name == 'interview_guide':
                content = json.dumps({"core_questions": ["Q1"], "deep_dive_questions": ["D1"]})
            elif prompt_name == 'learn_refutations':
                content = json.dumps({"refutations": [{"quote": "I didn't use it", "line": 2, "source": "interview_fake", "evidence": {"evidence_type": "quote", "content": "I didn't use it"}}]})
            elif prompt_name == 'learn_interview':
                content = json.dumps({"refutations": [{"quote": "I didn't use it", "line": 2, "source": "interview_fake", "evidence": {"evidence_type": "quote", "content": "I didn't use it"}}]})
            else:
                content = "{}"
        
        # Pydantic Validation
        data = json.loads(content)
        if prompt_name == 'draw_persona':
            DrawResponse(**data)
        elif prompt_name == 'explore_alternatives':
            ExploreResponse(**data)
        elif prompt_name == 'interview_guide':
            InterviewGuideResponse(**data)
        elif prompt_name in ['learn_refutations', 'learn_interview']:
            InterviewAnalysisResponse(**data)

        return LLMResponse(content=content, ai_completions=["mock_completion"], prompt_used=prompt_name, model_name='mock')

class ManualLLMProvider(LLMProvider):
    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt_name, context):
        file_path = self.export_dir / f"{prompt_name}_prompt.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'prompt_name': prompt_name, 'context': context, 'instructions': 'Please fill response.json'}, f, ensure_ascii=False)
        return LLMResponse(content=f"Exported to {file_path}. Use import-response to load.", ai_completions=[], prompt_used=prompt_name, model_name='manual')
