import pytest
from pathlib import Path
from needs_detector.core.services import DrawService, ExploreService, ProjectService
import yaml
import shutil

def test_input_difference(tmp_path):
    proj_a = tmp_path / "projA"
    proj_b = tmp_path / "projB"
    ProjectService.init_project(proj_a, "A")
    ProjectService.init_project(proj_b, "B")
    
    (proj_a / "idea.md").write_text("Idea A", encoding="utf-8")
    (proj_b / "idea.md").write_text("Idea B", encoding="utf-8")
    
    DrawService.draw(proj_a, "mock", "dataset_a")
    DrawService.draw(proj_b, "mock", "dataset_b")
    
    persona_a = list((proj_a / 'personas').glob('*.yaml'))[0]
    persona_b = list((proj_b / 'personas').glob('*.yaml'))[0]
    
    with open(persona_a, 'r', encoding='utf-8') as f:
        data_a = yaml.safe_load(f)
    with open(persona_b, 'r', encoding='utf-8') as f:
        data_b = yaml.safe_load(f)
        
    assert data_a['name'] != data_b['name']
    
    ExploreService.explore(proj_a, "mock", "dataset_a")
    ExploreService.explore(proj_b, "mock", "dataset_b")
    
    alt_a = list((proj_a / 'alternatives').glob('*.yaml'))[0]
    alt_b = list((proj_b / 'alternatives').glob('*.yaml'))[0]
    
    with open(alt_a, 'r', encoding='utf-8') as f:
        alt_data_a = yaml.safe_load(f)
    with open(alt_b, 'r', encoding='utf-8') as f:
        alt_data_b = yaml.safe_load(f)
        
    assert alt_data_a['direct_competition'] != alt_data_b['direct_competition']
