import pytest
import os
import sys
import subprocess
from pathlib import Path

def get_env():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(os.getcwd()) / "src")
    return env

def test_manual_validation_invalid_json(tmp_path):
    project_dir = tmp_path / "myproj"
    env = get_env()
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "init", "myproj", "--dir", str(tmp_path)], env=env)
    
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{bad", encoding="utf-8")
    
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "import-llm-response", str(invalid)], cwd=project_dir, capture_output=True, env=env)
    assert res.returncode == 1

def test_manual_validation_unknown_prompt(tmp_path):
    project_dir = tmp_path / "myproj"
    env = get_env()
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "init", "myproj", "--dir", str(tmp_path)], env=env)
    
    unknown = tmp_path / "unknown.json"
    import json
    with open(unknown, "w") as f:
        json.dump({"prompt_used": "unknown", "content": {}}, f)
        
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "import-llm-response", str(unknown)], cwd=project_dir, capture_output=True, env=env)
    assert res.returncode == 1

def test_manual_validation_bad_schema(tmp_path):
    project_dir = tmp_path / "myproj"
    env = get_env()
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "init", "myproj", "--dir", str(tmp_path)], env=env)
    
    bad = tmp_path / "bad.json"
    import json
    with open(bad, "w") as f:
        json.dump({"prompt_used": "draw_persona", "content": {"missing": 1}}, f)
        
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "import-llm-response", str(bad)], cwd=project_dir, capture_output=True, env=env)
    assert res.returncode == 1

def test_manual_validation_ai_completions_schema(tmp_path):
    import json
    import yaml
    from needs_detector.core.services import ProjectService, DrawService, ImportService

    project_dir = tmp_path / "project"
    ProjectService.init_project(project_dir, "project")
    DrawService.draw(project_dir, "manual")
    with open(project_dir / "manual_prompts" / "index.yaml", encoding="utf-8") as f:
        job = yaml.safe_load(f)[0]
    response = tmp_path / "response.json"
    response.write_text(json.dumps({
        "job_id": job["job_id"], "prompt_used": "draw_persona",
        "content": {"personas": []}, "ai_completions": [{"content": 123}]
    }), encoding="utf-8")
    with pytest.raises(Exception):
        ImportService.import_response(project_dir, str(response))
