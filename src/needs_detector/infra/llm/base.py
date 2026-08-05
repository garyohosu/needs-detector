import json
import os
import re
from pathlib import Path
from abc import ABC, abstractmethod
from needs_detector.domain.models.llm_models import (
    DrawResponse, ExploreResponse, InterviewGuideResponse, InterviewAnalysisResponse
)

import importlib.resources
from needs_detector.domain.models.exceptions import MockFixtureNotFoundError

class LLMResponse:
    def __init__(self, content, ai_completions, prompt_used, model_name, fixture_used=None):
        self.content = content
        self.ai_completions = ai_completions
        self.prompt_used = prompt_used
        self.model_name = model_name
        self.fixture_used = fixture_used

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt_name, context, fixture_key=None, project_dir=None):
        pass

class MockLLMProvider(LLMProvider):
    def _get_fixture_key(self, context: str, fixture_key_arg: str, project_dir: Path) -> str:
        if fixture_key_arg:
            return fixture_key_arg
            
        if project_dir and (project_dir / 'project.yaml').exists():
            try:
                with open(project_dir / 'project.yaml', 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                if 'mock_fixture_key' in data:
                    return data['mock_fixture_key']
            except Exception:
                pass

        match = re.search(r'FIXTURE_KEY:\s*([\w\-]+)', str(context))
        if match:
            return match.group(1)
            
        if "Persona A" in str(context):
            return "dataset_a"
        if "Persona B" in str(context):
            return "dataset_b"
            
        env_key = os.environ.get('MOCK_FIXTURE_KEY')
        if env_key:
            return env_key
        return "default"

    def generate(self, prompt_name, context, fixture_key=None, project_dir=None):
        import yaml
        actual_key = self._get_fixture_key(context, fixture_key, project_dir)
        filename = f"{actual_key}_{prompt_name}.json"
        
        try:
            fixture_res = importlib.resources.files('needs_detector.fixtures.llm').joinpath(filename)
            if not fixture_res.is_file():
                raise FileNotFoundError()
            content = fixture_res.read_text(encoding='utf-8')
        except FileNotFoundError:
            raise MockFixtureNotFoundError(f"Fixture {filename} not found.")

        data = json.loads(content)
        if prompt_name == 'draw_persona':
            DrawResponse(**data)
        elif prompt_name == 'explore_alternatives':
            ExploreResponse(**data)
        elif prompt_name == 'interview_guide':
            InterviewGuideResponse(**data)
        elif prompt_name in ['learn_refutations', 'learn_interview']:
            InterviewAnalysisResponse(**data)

        return LLMResponse(content=content, ai_completions=["mock_completion"], prompt_used=prompt_name, model_name='mock', fixture_used=filename)

class ManualLLMProvider(LLMProvider):
    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt_name, context, fixture_key=None, project_dir=None):
        file_path = self.export_dir / f"{prompt_name}_prompt.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'prompt_used': prompt_name, 'context': context, 'instructions': 'Please fill content object.'}, f, ensure_ascii=False)
        return LLMResponse(content=f"Exported to {file_path}. Use import-response to load.", ai_completions=[], prompt_used=prompt_name, model_name='manual')

