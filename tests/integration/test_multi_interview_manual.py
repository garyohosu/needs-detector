import pytest
from pathlib import Path
from needs_detector.core.services import ProjectService, InterviewService, LearnService, ImportService
import json

def test_multi_interview_manual(tmp_path):
    project_dir = tmp_path / "proj"
    ProjectService.init_project(project_dir, "test_proj")
    
    iv1 = project_dir / "interviews" / "interview_1.yaml"
    iv2 = project_dir / "interviews" / "interview_2.yaml"
    
    # Mock add_interview
    iv1.write_text("content: 'line1\\nline2'", encoding="utf-8")
    iv2.write_text("content: 'lineA\\nlineB'", encoding="utf-8")
    
    # Run learn with manual provider
    LearnService.learn(project_dir, "manual")
    
    import yaml
    with open(project_dir / "project.yaml", "r", encoding="utf-8") as f:
        proj = yaml.safe_load(f)
    assert proj["status"]["step4_learn"] == "waiting_llm"
    
    # Generate mock response for iv1
    with open(project_dir / "manual_prompts" / "index.yaml", "r", encoding="utf-8") as f:
        jobs = yaml.safe_load(f)
    
    assert len(jobs) == 2
    job1 = jobs[0]
    job2 = jobs[1]
    
    resp1 = {
        "prompt_used": "learn_interview",
        "job_id": job1["job_id"],
        "target": job1["target"],
        "content": {
            "refutations": [],
            "cpf_evidence": {}
        }
    }
    
    resp1_path = tmp_path / "resp1.json"
    resp1_path.write_text(json.dumps(resp1), encoding="utf-8")
    
    ImportService.import_response(project_dir, str(resp1_path))
    
    with open(project_dir / "project.yaml", "r", encoding="utf-8") as f:
        proj = yaml.safe_load(f)
    assert proj["status"]["step4_learn"] == "waiting_llm"
    
    resp2 = {
        "prompt_used": "learn_interview",
        "job_id": job2["job_id"],
        "target": job2["target"],
        "content": {
            "refutations": [],
            "cpf_evidence": {}
        }
    }
    resp2_path = tmp_path / "resp2.json"
    resp2_path.write_text(json.dumps(resp2), encoding="utf-8")
    
    ImportService.import_response(project_dir, str(resp2_path))
    
    with open(project_dir / "project.yaml", "r", encoding="utf-8") as f:
        proj = yaml.safe_load(f)
    assert proj["status"]["step4_learn"] == "completed"
    assert proj["status"]["step3_listen"] == "completed"
