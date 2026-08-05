import pytest
import tempfile
import subprocess
import sys
import os
from pathlib import Path

def test_mock_works_outside_repo():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(os.getcwd()) / "src")
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run([sys.executable, "-m", "needs_detector.cli.main",
            "init", "proj", "--dir", tmpdir],
            capture_output=True, text=True, env=env)
        assert result.returncode == 0
        proj_dir = os.path.join(tmpdir, "proj")
        
        result = subprocess.run([sys.executable, "-m", "needs_detector.cli.main",
            "draw", "--provider", "mock", "--fixture-key", "dataset_a"],
            capture_output=True, text=True, cwd=proj_dir, env=env)
        assert result.returncode == 0

def test_missing_fixture_raises_error():
    from needs_detector.infra.llm.base import MockLLMProvider
    from needs_detector.domain.models.exceptions import MockFixtureNotFoundError
    provider = MockLLMProvider()
    with pytest.raises(MockFixtureNotFoundError):
        provider.generate("draw_persona", "context", fixture_key="non_existent")

def test_manual_workflow(tmp_path):
    project_dir = tmp_path / "myproj"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(os.getcwd()) / "src") if 'PYTHONPATH' not in os.environ else os.environ["PYTHONPATH"]
    
    # Init
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "init", "myproj", "--dir", str(tmp_path)], env=env, capture_output=True, text=True)
    assert res.returncode == 0
    
    # Draw manual
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "draw", "--provider", "manual"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    
    import yaml
    with open(project_dir / "project.yaml", "r", encoding="utf-8") as f:
        st = yaml.safe_load(f)["status"]
        assert st["step1_draw"] == "waiting_llm"
        
    # Explore manual
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "explore", "--provider", "manual"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    
    # Learn manual
    iv = project_dir / "interviews" / "interview_1.yaml"
    iv.parent.mkdir(exist_ok=True)
    with open(iv, "w", encoding="utf-8") as f:
        yaml.dump({"content": "foo\nbar", "refutations": [], "target": "1"}, f)
        
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "learn", "--provider", "manual"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
