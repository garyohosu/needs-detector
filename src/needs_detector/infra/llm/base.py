import json
import hashlib
from pathlib import Path
from abc import ABC, abstractmethod

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
    def generate(self, prompt_name, context):
        ctx_hash = hashlib.md5(str(context).encode()).hexdigest()[:6]
        content = ""
        
        if prompt_name == 'draw_persona':
            content = json.dumps({
                "personas": [{
                    "id": f"p_{ctx_hash}",
                    "name": f"Persona Name {ctx_hash}",
                    "situation": "Busy professional",
                    "jobs": {
                        "functional": "Get tasks done",
                        "emotional": "Feel productive",
                        "social": "Look reliable"
                    },
                    "impediments": "Too many tools",
                    "current_coping": "Using pen and paper",
                    "dissatisfaction": "Hard to search",
                    "evidence_type": "Observation",
                    "source_reference": "Idea/Source text",
                    "questions_to_verify": ["How often do you lose paper?"]
                }]
            })
        elif prompt_name == 'explore_alternatives':
            content = json.dumps({
                "direct_competition": [{"name": f"Direct App {ctx_hash}", "benefits": "Syncs", "problems": "Complex", "cost_time": "10 USD"}],
                "indirect_alternatives": [{"name": f"Indirect App {ctx_hash}", "benefits": "Easy", "problems": "Manual", "cost_time": "Free"}],
                "non_consumption": [{"name": f"Do nothing {ctx_hash}", "benefits": "No effort", "problems": "Forget things", "cost_time": "0"}]
            })
        elif prompt_name == 'interview_guide':
            content = json.dumps({
                "core_questions": [
                    "What is the hardest part about this job?",
                    "When was the last time you tried to solve this problem?",
                    "Why was that hard?",
                    "What, if anything, have you done to try to solve this problem?",
                    "What don't you love about the solutions you've tried?"
                ],
                "deep_dive_questions": ["Tell me more about the specific event.", "How much time did you spend?"]
            })
        elif prompt_name == 'learn_refutations':
            # Extract refutations using JSON. Just dummy returning something.
            content = json.dumps({
                "refutations": [
                    {"quote": f"I didn't use it {ctx_hash}", "line": 2, "source": "interview_fake"}
                ]
            })
        
        return LLMResponse(content=content, ai_completions=["mock_completion_1"], prompt_used=prompt_name, model_name='mock')

class ManualLLMProvider(LLMProvider):
    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, prompt_name, context):
        file_path = self.export_dir / f"{prompt_name}_prompt.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'prompt_name': prompt_name, 'context': context, 'instructions': 'Please fill response.json'}, f)
        return LLMResponse(content=f"Exported to {file_path}. Use import-response to load.", ai_completions=[], prompt_used=prompt_name, model_name='manual')
    
    def import_response(self, json_file_path: Path):
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return LLMResponse(content=data.get('content', ''), ai_completions=data.get('ai_completions', []), prompt_used=data.get('prompt_used', 'imported'), model_name='manual')

