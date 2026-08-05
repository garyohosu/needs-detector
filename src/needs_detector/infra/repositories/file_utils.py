import os
from pathlib import Path

def atomic_write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix('.tmp')
    tmp_path.write_text(content, encoding='utf-8')
    tmp_path.replace(path)
