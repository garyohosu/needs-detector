import pytest
from pathlib import Path
from needs_detector.infra.repositories.file_utils import validate_project_path, PathSafetyError

def test_path_safety_outside(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    
    outside_path = tmp_path / "outside.txt"
    with pytest.raises(PathSafetyError):
        validate_project_path(outside_path, project_root)

def test_path_safety_inside(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    
    inside_path = project_root / "inside.txt"
    validate_project_path(inside_path, project_root) # Should not raise
