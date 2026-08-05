import json
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

from needs_detector.core.services import DoctorService, NextService, ProjectService


def _env():
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(os.getcwd()) / 'src')
    return env


def test_doctor_normal_and_json(tmp_path):
    project = tmp_path / 'project'
    ProjectService.init_project(project, 'project')
    result = DoctorService.diagnose(project)
    assert result['status'] == 'warning'
    assert result['errors'] == []
    completed = subprocess.run([sys.executable, '-m', 'needs_detector.cli.main', 'doctor', '--json'],
                               cwd=project, env=_env(), capture_output=True, text=True)
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert set(('status', 'errors', 'warnings', 'checks', 'next_actions')) <= payload.keys()


def test_doctor_detects_broken_yaml_and_source(tmp_path):
    project = tmp_path / 'project'
    ProjectService.init_project(project, 'project')
    (project / 'project.yaml').write_text('status: [broken', encoding='utf-8')
    assert DoctorService.diagnose(project)['status'] == 'error'
    ProjectService.init_project(project, 'project')
    (project / 'sources' / 'index.yaml').write_text('sources:\n  - file_name: missing.md\n', encoding='utf-8')
    result = DoctorService.diagnose(project)
    assert any('missing.md' in item for item in result['errors'])


def test_doctor_detects_quote_and_state_errors(tmp_path):
    project = tmp_path / 'project'
    ProjectService.init_project(project, 'project')
    interview = project / 'interviews' / 'interview_x.yaml'
    interview.write_text(yaml.safe_dump({'content': 'one', 'refutations': [{'quote': 'nope', 'line': 2}]}), encoding='utf-8')
    result = DoctorService.diagnose(project)
    assert any('interview:interview_x.yaml' in item for item in result['errors'])
    interview.unlink()
    with open(project / 'project.yaml', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    data['status']['step4_learn'] = 'completed'
    with open(project / 'project.yaml', 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f)
    assert any('インタビュー0件' in item for item in DoctorService.diagnose(project)['errors'])


def test_next_respects_human_gate_and_manual_waiting(tmp_path):
    project = tmp_path / 'project'
    ProjectService.init_project(project, 'project')
    first = NextService.suggest(project)
    assert any('add-idea' in action for action in first['actions'])
    (project / 'idea.md').write_text('idea', encoding='utf-8')
    (project / 'interviews' / 'interview_x.yaml').write_text(
        yaml.safe_dump({'content': 'line', 'refutations': [], 'target': 'x'}), encoding='utf-8')
    subprocess.run([sys.executable, '-m', 'needs_detector.cli.main', 'learn', '--provider', 'manual'],
                   cwd=project, env=_env(), check=True, capture_output=True, text=True)
    result = NextService.suggest(project)
    assert any('job_id=' in action and 'target=interview_x' in action for action in result['actions'])
    assert not any('検証完了' in action for action in result['actions'])


def test_synthetic_and_real_classification_are_not_claimed_verified(tmp_path):
    synthetic = tmp_path / 'synthetic'
    ProjectService.init_project(synthetic, 'synthetic')
    subprocess.run([sys.executable, '-m', 'needs_detector.cli.main', 'draw', '--provider', 'mock', '--fixture-key', 'dataset_a'],
                   cwd=synthetic, env=_env(), check=True)
    subprocess.run([sys.executable, '-m', 'needs_detector.cli.main', 'report'], cwd=synthetic, env=_env(), check=True)
    report = (synthetic / 'reports' / 'final_report.md').read_text(encoding='utf-8')
    assert 'データ区分: synthetic' in report
    assert '実顧客検証' in report

    real = tmp_path / 'real'
    ProjectService.init_project(real, 'real')
    source = tmp_path / 'real-interview.md'
    source.write_text('実際の出来事', encoding='utf-8')
    subprocess.run([sys.executable, '-m', 'needs_detector.cli.main', 'add-interview', str(source), '--data-classification', 'real'],
                   cwd=real, env=_env(), check=True)
    assert DoctorService.diagnose(real)['status'] == 'ok'
    assert NextService.suggest(real)['data_classification'] == 'real'


def test_doctor_detects_stale_report_and_root_guidance():
    root = Path(__file__).parents[2]
    assert (root / 'AGENTS.md').read_text(encoding='utf-8').find('.agents/AGENTS.md') >= 0
    assert 'instructions/' in (root / 'AGENTS.md').read_text(encoding='utf-8')
