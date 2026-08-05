import pytest
import os
from pathlib import Path
from needs_detector.core.services import ProjectService, DrawService, ExploreService, InterviewService, LearnService, ReportService, HumanGateError

def test_cli_init_success(tmp_path):
    target = tmp_path / "myproj"
    ProjectService.init_project(target, "myproj")
    assert (target / "project.yaml").exists()
    assert (target / "sources" / "index.yaml").exists()

def test_cli_full_workflow(tmp_path):
    target = tmp_path / "myproj"
    ProjectService.init_project(target, "myproj")
    
    idea_file = tmp_path / "idea.txt"
    idea_file.write_text("my idea", encoding="utf-8")
    ProjectService.add_idea(target, str(idea_file))
    assert (target / "idea.md").exists()
    
    DrawService.draw(target, "mock")
    assert (target / "personas" / "persona_1.yaml").exists()
    
    ExploreService.explore(target, "mock")
    assert (target / "alternatives" / "alternatives.yaml").exists()
    
    InterviewService.generate_guide(target)
    assert (target / "interviews" / "guide.md").exists()
    
    interview_file = tmp_path / "interview.txt"
    interview_file.write_text("山田太郎 is speaking", encoding="utf-8")
    InterviewService.add_interview(target, str(interview_file))
    assert (target / "interviews" / "interview_interview.yaml").exists()
    
    LearnService.learn(target, "mock")
    ReportService.generate_report(target)
    assert (target / "reports" / "final_report.md").exists()
