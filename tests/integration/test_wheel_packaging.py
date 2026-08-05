import os
import subprocess
import sys
import shutil
from pathlib import Path
import pytest

def test_wheel_packaging(tmp_path):
    project_root = Path(__file__).parent.parent.parent.resolve()
    
    # 1. Build a wheel
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "-w", str(build_dir), str(project_root)], check=True)
    
    wheels = list(build_dir.glob("*.whl"))
    assert len(wheels) == 1, "Expected exactly one wheel file"
    wheel_file = wheels[0]
    
    import zipfile
    with zipfile.ZipFile(wheel_file) as zf:
        assert any(n.startswith('needs_detector/fixtures/llm/') for n in zf.namelist()), "Fixtures not found in wheel"

    # 2. Install wheel to a temp target dir
    install_dir = tmp_path / "install"
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--target", str(install_dir), str(wheel_file)], check=True)
    
    # 3. Create a test script outside the repo
    test_script = tmp_path / "test_import.py"
    test_script.write_text("""
import sys
from pathlib import Path

# Add install_dir to sys.path
sys.path.insert(0, sys.argv[1])

from needs_detector.infra.llm.base import MockLLMProvider
provider = MockLLMProvider()
# Verify fixture loads successfully
try:
    resp = provider.generate("draw_persona", "Some Context", "dataset_a")
    if resp.prompt_used != 'draw_persona':
        sys.exit(1)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)
""", encoding="utf-8")

    # 4. Run the test script without src in PYTHONPATH
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        del env["PYTHONPATH"]
        
    result = subprocess.run([sys.executable, str(test_script), str(install_dir)], 
                            cwd=str(tmp_path), env=env, capture_output=True, text=True)
                            
    assert result.returncode == 0, f"Script failed: {result.stdout} {result.stderr}"
    assert "SUCCESS" in result.stdout
