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
    
    # Source
    src_file = tmp_path / "source.md"
    src_file.write_text("Hello Source", encoding="utf-8")
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "add-source", str(src_file)], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    
    # Draw
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "draw"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    
    # Explore
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "explore"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    
    # Interview Guide
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "interview-guide"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    
    # Learn without interviews (Human gate test)
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "learn"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode != 0
    
    # Add Interview
    iv_file = tmp_path / "iv.md"
    iv_file.write_text("line 1\nI didn't use it\nline 3\n", encoding="utf-8")
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "add-interview", str(iv_file)], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    
    # Learn
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "learn"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    
    # Report
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "report"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
    assert (project_dir / "reports" / "final_report.md").exists()
    
    # Status
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "status"], cwd=project_dir, env=env, capture_output=True, text=True)
    assert res.returncode == 0
