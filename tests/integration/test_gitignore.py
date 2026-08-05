import os
from pathlib import Path

def test_gitignore_dynamic():
    project_root = Path(os.getcwd())
    gitignore_path = project_root / '.gitignore'
    assert gitignore_path.exists()
    content = gitignore_path.read_text(encoding='utf-8')
    assert '.env' in content
    assert 'sources/' in content
    assert 'interviews/' in content
    assert 'reports/' in content
    assert '.pytest_cache' in content
