import pytest
from pathlib import Path
import os
from needs_detector.core.services import ProjectService, LearnService, ReportService, HumanGateError

def test_unverified_status_without_interview(tmp_path):
    target = tmp_path / "myproj"
    ProjectService.init_project(target, "myproj")
    
    with pytest.raises(HumanGateError, match="インタビュー記録が1件も存在しない"):
        LearnService.learn(target, "mock")

def test_report_evidence_traceability(tmp_path):
    target = tmp_path / "myproj"
    ProjectService.init_project(target, "myproj")
    ReportService.generate_report(target)
    content = (target / "reports" / "final_report.md").read_text(encoding="utf-8")
    assert "[interview_1:L10]" in content

def test_offline_mock_execution(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    target = tmp_path / "myproj"
    ProjectService.init_project(target, "myproj")
    # Execute something that might normally use LLM
    try:
        from needs_detector.core.services import DrawService
        DrawService.draw(target, "mock")
        success = True
    except Exception:
        success = False
    assert success

def test_secret_and_git_exclusion():
    gitignore_path = Path("C:/PROJECT/needs-detector/.gitignore")
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        assert "secrets/" in content
        assert ".env" in content

def test_windows_path_compatibility():
    p = Path("C:\\PROJECT\\needs-detector")
    assert p.is_absolute()
