import json
import os
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import uuid
import yaml
import importlib.resources
from needs_detector.domain.models.llm_models import (
    DrawResponse, ExploreResponse, InterviewGuideResponse, InterviewAnalysisResponse
)

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
            except yaml.YAMLError as exc:
                raise ValueError(f"YAML parsing error in project.yaml: {exc}") from exc
            
            if not isinstance(data, dict):
                raise TypeError("project.yaml root must be a dictionary")

            if 'mock_fixture_key' in data:
                value = data['mock_fixture_key']
                if not isinstance(value, str) or not value.strip():
                    raise TypeError("project.yaml mock_fixture_key must be a non-empty string")
                return value.strip()
            
        env_key = os.environ.get('MOCK_FIXTURE_KEY')
        if env_key:
            return env_key
        return "default"

    def generate(self, prompt_name, context, fixture_key=None, project_dir=None):
        actual_key = self._get_fixture_key(context, fixture_key, project_dir)
        filename = f"{actual_key}_{prompt_name}.json"
        
        try:
            fixture_res = importlib.resources.files('needs_detector.fixtures.llm').joinpath(filename)
            if not fixture_res.is_file():
                raise FileNotFoundError()
            content = fixture_res.read_text(encoding='utf-8')
        except FileNotFoundError as exc:
            raise MockFixtureNotFoundError(f"Fixture {filename} not found.") from exc

        data = json.loads(content)
        if prompt_name == 'draw_persona':
            DrawResponse(**data)
        elif prompt_name == 'explore_alternatives':
            ExploreResponse(**data)
        elif prompt_name == 'interview_guide':
            InterviewGuideResponse(**data)
        elif prompt_name in ['learn_refutations', 'learn_interview']:
            InterviewAnalysisResponse(**data)

        if project_dir:
            audit_file = Path(project_dir) / 'reports' / 'mock_fixture_audit.yaml'
            audit_file.parent.mkdir(parents=True, exist_ok=True)
            audit = []
            if audit_file.exists():
                with open(audit_file, 'r', encoding='utf-8') as f:
                    audit = yaml.safe_load(f) or []
            audit.append({'prompt_used': prompt_name, 'fixture_key': actual_key, 'fixture_file': filename})
            with open(audit_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump(audit, f, allow_unicode=True)

        return LLMResponse(content=content, ai_completions=data.get('ai_completions', []), prompt_used=prompt_name, model_name='mock', fixture_used=filename)

class ManualLLMProvider(LLMProvider):
    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.export_dir / "index.yaml"
        if not self.index_file.exists():
            with open(self.index_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump([], f)

    def generate(self, prompt_name, context, fixture_key=None, project_dir=None):
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
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'job_id': job_id, 'prompt_used': prompt_name, 'target': target,
                       'context': context, 'instructions': 'Return JSON with content and ai_completions.'},
                      f, ensure_ascii=False, indent=2)
            
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
            yaml.safe_dump(jobs, f, allow_unicode=True)
            
        return LLMResponse(content=f"Job {job_id} exported to {file_path}. Use import-llm-response to load.", ai_completions=[], prompt_used=prompt_name, model_name='manual')

