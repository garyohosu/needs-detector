import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

from needs_detector.core.services import DoctorService, InterviewService, NextService, ProjectService, ReportService


def env():
    values = os.environ.copy()
    values['PYTHONPATH'] = str(Path(os.getcwd()) / 'src')
    return values


def make_project(tmp_path, name='project'):
    project = tmp_path / name
    ProjectService.init_project(project, name)
    return project


def test_normal_add_source_is_doctor_ok_and_next_counts_entries(tmp_path):
    project = make_project(tmp_path)
    source = tmp_path / 'source.md'
    source.write_text('source text', encoding='utf-8')
    subprocess.run([sys.executable, '-m', 'needs_detector.cli.main', 'add-source', str(source)],
                   cwd=project, env=env(), check=True)
    assert (project / 'sources' / 'source.md').exists()
    diagnosis = DoctorService.diagnose(project)
    source_check = next(item for item in diagnosis['checks'] if item['name'] == 'sources')
    assert source_check['status'] == 'ok'
    assert not diagnosis['errors']
    cli_doctor = subprocess.run([sys.executable, '-m', 'needs_detector.cli.main', 'doctor', '--json'],
                                cwd=project, env=env(), capture_output=True, text=True)
    assert cli_doctor.returncode == 0
    assert json.loads(cli_doctor.stdout)['status'] in {'ok', 'warning'}
    actions = NextService.suggest(project)['actions']
    assert not any('add-source' in action for action in actions)


def test_index_only_next_add_source_and_source_path_rejections(tmp_path):
    project = make_project(tmp_path)
    assert any('add-source' in action for action in NextService.suggest(project)['actions'])
    index = project / 'sources' / 'index.yaml'
    for file_name in ('../outside.md', 'C:\\outside.md', '\\\\server\\share\\file.md'):
        index.write_text(yaml.safe_dump({'sources': [{'id': 'src', 'file_name': file_name}]}), encoding='utf-8')
        result = DoctorService.diagnose(project)
        assert result['status'] == 'error'


def test_raw_interview_hash_and_real_quote_reference(tmp_path):
    project = make_project(tmp_path)
    input_file = tmp_path / 'customer.md'
    input_file.write_text('first line\nCustomer quote\nlast line\n', encoding='utf-8')
    InterviewService.add_interview(project, str(input_file), 'real')
    raw = project / 'interviews' / 'raw' / 'customer.md'
    derived = project / 'interviews' / 'interview_customer.yaml'
    data = yaml.safe_load(derived.read_text(encoding='utf-8'))
    assert raw.exists()
    assert data['source_file'] == 'interviews/raw/customer.md'
    assert data['source_sha256'] == hashlib.sha256(raw.read_bytes()).hexdigest()
    data['refutations'] = [{'quote': 'Customer quote', 'line': 2}]
    derived.write_text(yaml.safe_dump(data, allow_unicode=True), encoding='utf-8')
    ReportService.generate_report(project)
    report = (project / 'reports' / 'final_report.md').read_text(encoding='utf-8')
    assert '[interviews/raw/customer.md:L2]' in report
    assert 'Customer quote' in raw.read_text(encoding='utf-8').splitlines()[1]
    assert DoctorService.diagnose(project)['status'] == 'ok'


def test_raw_change_delete_and_duplicate_are_detected(tmp_path):
    project = make_project(tmp_path)
    input_file = tmp_path / 'customer.md'
    input_file.write_text('original', encoding='utf-8')
    InterviewService.add_interview(project, str(input_file), 'real')
    raw = project / 'interviews' / 'raw' / 'customer.md'
    raw.write_text('changed', encoding='utf-8')
    assert any('hash mismatch' in item for item in DoctorService.diagnose(project)['errors'])
    raw.unlink()
    assert any('raw interview missing' in item for item in DoctorService.diagnose(project)['errors'])
    try:
        InterviewService.add_interview(project, str(input_file), 'real')
    except ValueError as exc:
        assert 'already exists' in str(exc)
    else:
        raise AssertionError('duplicate interview was accepted')


def test_classification_matrix_and_synthetic_project_fallback(tmp_path):
    cases = {
        'real': ['real'], 'synthetic': ['synthetic'], 'unknown': ['unknown'],
        'real_synthetic': ['real', 'synthetic'], 'real_unknown': ['real', 'unknown'],
        'synthetic_unknown': ['synthetic', 'unknown'],
    }
    for name, classifications in cases.items():
        project = make_project(tmp_path, name)
        for index, classification in enumerate(classifications):
            source = tmp_path / f'{name}-{index}.md'
            source.write_text(f'{classification} interview', encoding='utf-8')
            InterviewService.add_interview(project, str(source), classification)
        result = DoctorService.diagnose(project)
        expected = name if name in {'real', 'synthetic', 'unknown'} else 'mixed'
        assert result['data_classification'] == expected
        assert NextService.suggest(project)['data_classification'] == expected
        ReportService.generate_report(project)
        report = (project / 'reports' / 'final_report.md').read_text(encoding='utf-8')
        assert f'データ区分: {expected}' in report
        if expected != 'real':
            assert '実顧客検証' in report

    synthetic_project = make_project(tmp_path, 'synthetic_project')
    with open(synthetic_project / 'project.yaml', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    data['data_classification'] = 'synthetic'
    with open(synthetic_project / 'project.yaml', 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f)
    assert DoctorService.diagnose(synthetic_project)['data_classification'] == 'synthetic'


def test_legacy_interview_is_warning_not_destructive(tmp_path):
    project = make_project(tmp_path)
    legacy = project / 'interviews' / 'interview_legacy.yaml'
    legacy.write_text(yaml.safe_dump({'content': 'legacy line', 'refutations': [], 'target': 'legacy'}), encoding='utf-8')
    result = DoctorService.diagnose(project)
    assert not result['errors']
    assert any('legacy interview' in warning for warning in result['warnings'])
