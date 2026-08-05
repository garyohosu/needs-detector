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
            import yaml
            with open(project_dir / 'project.yaml', 'r', encoding='utf-8') as f:
                try:
                    data = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ValueError(f"YAML parsing error in project.yaml: {e}")
            
            if not isinstance(data, dict):
                raise TypeError("project.yaml root must be a dictionary")

            if 'mock_fixture_key' in data:
                return data['mock_fixture_key']
            
        import os
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

        return LLMResponse(content=content, ai_completions=data.get('ai_completions', []), prompt_used=prompt_name, model_name='mock', fixture_used=filename)

class ManualLLMProvider(LLMProvider):
    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.export_dir / "index.yaml"
        if not self.index_file.exists():
            import yaml
            with open(self.index_file, 'w', encoding='utf-8') as f:
                yaml.dump([], f)

    def generate(self, prompt_name, context, fixture_key=None, project_dir=None):
        import uuid
        import yaml
        from datetime import datetime, timezone
        
        job_id = str(uuid.uuid4())
        job_dir = self.export_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        target = None
        if prompt_name == 'learn_interview':
            # Extract target from context, e.g. "Target:interview_foo\nContent:..."
            lines = str(context).splitlines()
            for line in lines:
                if line.startswith("Target:"):
                    target = line.split("Target:", 1)[1].strip()
                    break

        file_path = job_dir / "request.json"
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'prompt_used': prompt_name, 'context': context, 'instructions': 'Please fill content object.'}, f, ensure_ascii=False)
            
        with open(self.index_file, 'r', encoding='utf-8') as f:
            jobs = yaml.safe_load(f) or []
            
        job_record = {
            'job_id': job_id,
            'prompt_used': prompt_name,
            'target': target,
            'status': 'waiting_llm',
            'prompt_file': f"{job_id}/request.json",
            'response_file': None,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'imported_at': None
        }
        jobs.append(job_record)
        with open(self.index_file, 'w', encoding='utf-8') as f:
            yaml.dump(jobs, f)
            
        return LLMResponse(content=f"Job {job_id} exported to {file_path}. Use import-llm-response to load.", ai_completions=[], prompt_used=prompt_name, model_name='manual')

