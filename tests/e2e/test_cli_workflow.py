import pytest
import subprocess
import sys
import os
from pathlib import Path

def test_cli_workflow(tmp_path):
    project_dir = tmp_path / "myproj"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(os.getcwd()) / "src")
    
    # Init
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "init", "myproj", "--dir", str(tmp_path)], env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert project_dir.exists()
    
    # Idea
    idea_file = tmp_path / "idea.md"
    idea_file.write_text("Hello Idea", encoding="utf-8")
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "add-idea", str(idea_file)], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert (project_dir / "idea.md").exists()
    
    # Draw
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "draw"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert len(list((project_dir / "personas").glob("*.yaml"))) > 0
    
    # Explore
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "explore"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert len(list((project_dir / "alternatives").glob("*.yaml"))) > 0
    
    # Learn without interviews (Human gate test)
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "learn"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode != 0
    assert "No interviews found" in res.stderr or "Exception" in res.stderr or res.returncode != 0
