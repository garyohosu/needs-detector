import os
from pathlib import Path

class PathSafetyError(Exception):
    pass

def validate_project_path(target_path: Path, project_root: Path):
    target = Path(target_path).resolve()
    root = Path(project_root).resolve()
    if not target.is_relative_to(root):
        raise PathSafetyError(f"Path {target} is outside project root {root}")

def atomic_write(path: Path, content: str, project_root: Path = None):
    if project_root:
        validate_project_path(path, project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix('.tmp')
    tmp_path.write_text(content, encoding='utf-8')
    tmp_path.replace(path)

