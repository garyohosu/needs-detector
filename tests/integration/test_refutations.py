import pytest
from pathlib import Path
from needs_detector.core.services import InterviewService, LearnService, ProjectService
import yaml

def test_refutations(tmp_path):
    project_dir = tmp_path / "project"
    ProjectService.init_project(project_dir, "test")
    
    interview_file = tmp_path / "interview_001.md"
    interview_file.write_text("Hello\nI didn't use it\nGood\nIt took me 10 hours and 50 dollars.\n", encoding="utf-8")
    
    InterviewService.add_interview(project_dir, str(interview_file))
    LearnService.learn(project_dir, "mock")
    
    yaml_path = project_dir / "interviews" / "interview_interview_001.yaml"
    assert yaml_path.exists()
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    refs = data.get('refutations', [])
    assert len(refs) > 0
    # MockLLMProvider returns line 2 by default
    assert refs[0]['line'] == 2
