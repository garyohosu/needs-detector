import pytest
import os
import subprocess
import sys
from pathlib import Path

def get_env():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(os.getcwd()) / "src")
    return env

def test_report_content(tmp_path):
    env = get_env()
    project_dir = tmp_path / "proj_report"
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "init", "proj_report", "--dir", str(tmp_path)], env=env)
    
    # Dataset A
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "draw", "--fixture-key", "dataset_a"], cwd=project_dir, env=env)
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "explore", "--fixture-key", "dataset_a"], cwd=project_dir, env=env)
    
    iv_file = project_dir / "interviews" / "interview_01.yaml"
    iv_file.parent.mkdir(exist_ok=True)
    iv_file.write_text("content: \"User said X\\nI didn't use it\\nAlternative Y It was slow\"\n", encoding="utf-8")
    
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "learn", "--fixture-key", "dataset_a"], cwd=project_dir, env=env)
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "report"], cwd=project_dir, env=env)
    
    report = (project_dir / "reports" / "final_report.md").read_text(encoding="utf-8")
    assert "タスク管理ペルソナA" in report
    
    assert "interview_" in report
    assert "real_problem" in report
    assert "first_mover" in report
    assert "current_alternative" in report
    assert "AI補完" in report
    
    # Dataset B
    project_dir2 = tmp_path / "proj_report2"
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "init", "proj_report2", "--dir", str(tmp_path)], env=env)
    
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "draw", "--fixture-key", "dataset_b"], cwd=project_dir2, env=env)
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "explore", "--fixture-key", "dataset_b"], cwd=project_dir2, env=env)
    
    iv_file2 = project_dir2 / "interviews" / "interview_02.yaml"
    iv_file2.parent.mkdir(exist_ok=True)
    iv_file2.write_text("content: \"Some text\\nI didn't use it\\nAnother alternative\"\n", encoding="utf-8")
    
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "learn", "--fixture-key", "dataset_b"], cwd=project_dir2, env=env)
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "report"], cwd=project_dir2, env=env)
    
    report2 = (project_dir2 / "reports" / "final_report.md").read_text(encoding="utf-8")
    assert "採用ペルソナB" in report2
    
    # Check semantic difference
    assert "タスク管理" not in report2
    assert report != report2

def test_multiple_personas_in_same_report(tmp_path):
    import yaml
    env = get_env()
    project_dir = tmp_path / "proj_multi"
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "init", "proj_multi", "--dir", str(tmp_path)], env=env)
    
    # Create two personas directly
    personas_dir = project_dir / "personas"
    personas_dir.mkdir(exist_ok=True, parents=True)
    
    p1 = {"id": "p1", "name": "Persona Alpha", "questions_to_verify": ["Q1 from Alpha"]}
    p2 = {"id": "p2", "name": "Persona Beta", "questions_to_verify": ["Q2 from Beta"]}
    
    with open(personas_dir / "p1.yaml", 'w', encoding='utf-8') as pf:
        yaml.dump(p1, pf)
    with open(personas_dir / "p2.yaml", 'w', encoding='utf-8') as pf:
        yaml.dump(p2, pf)
        
    subprocess.run([sys.executable, "-m", "needs_detector.cli.main", "report"], cwd=project_dir, env=env)
    
    report = (project_dir / "reports" / "final_report.md").read_text(encoding="utf-8")
    
    assert "Persona Alpha" in report
    assert "Persona Beta" in report
    assert "[p1] Q1 from Alpha" in report
    assert "[p2] Q2 from Beta" in report
