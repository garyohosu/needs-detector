import pytest
import os
import yaml
from pathlib import Path
from needs_detector.infra.llm.base import MockLLMProvider
from needs_detector.domain.models.exceptions import MockFixtureNotFoundError

def test_mock_fixture_key_from_project_yaml(tmp_path):
    project_dir = tmp_path
    with open(project_dir / "project.yaml", "w", encoding="utf-8") as f:
        yaml.dump({"mock_fixture_key": "dataset_b"}, f)
    
    provider = MockLLMProvider()
    key = provider._get_fixture_key("some context", None, project_dir)
    assert key == "dataset_b"

def test_mock_fixture_key_cli_overrides_yaml(tmp_path):
    project_dir = tmp_path
    with open(project_dir / "project.yaml", "w", encoding="utf-8") as f:
        yaml.dump({"mock_fixture_key": "dataset_b"}, f)
    
    provider = MockLLMProvider()
    key = provider._get_fixture_key("some context", "dataset_a", project_dir)
    assert key == "dataset_a"

def test_mock_fixture_key_invalid_yaml(tmp_path):
    project_dir = tmp_path
    with open(project_dir / "project.yaml", "w", encoding="utf-8") as f:
        f.write("mock_fixture_key: [")
    
    provider = MockLLMProvider()
    with pytest.raises(ValueError, match="YAML parsing error in project.yaml"):
        provider._get_fixture_key("some context", None, project_dir)

def test_mock_fixture_key_unknown_key_raises_error(tmp_path):
    project_dir = tmp_path
    provider = MockLLMProvider()
    with pytest.raises(MockFixtureNotFoundError):
        provider.generate("draw_persona", "some context", "unknown_fixture_key", project_dir)
