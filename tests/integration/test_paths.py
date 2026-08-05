import pytest
import os
from pathlib import Path
from needs_detector.core.services import ProjectService

def test_utf8_and_space_paths(tmp_path):
    # test paths with spaces and utf8
    project_dir = tmp_path / "My Project ã\x81\x82"
    ProjectService.init_project(project_dir, "test")
    
    idea_file = tmp_path / "idea ã\x81\x82.md"
    idea_file.write_text("ã\x81\x93ã\x82\x93ã\x81«ã\x81¡ã\x81¯", encoding="utf-8")
    
    ProjectService.add_idea(project_dir, str(idea_file))
    
    assert (project_dir / "idea.md").exists()
    assert (project_dir / "idea.md").read_text(encoding="utf-8") == "ã\x81\x93ã\x82\x93ã\x81«ã\x81¡ã\x81¯"
