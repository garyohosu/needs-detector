import hashlib
import json
import ntpath
import re
import shutil
import json as json_module
from datetime import datetime, timezone
from pathlib import Path

import yaml
from pydantic import ValidationError

from needs_detector.domain.models.exceptions import QuoteValidationError
from needs_detector.domain.models.llm_models import (
    AICompletion, DrawResponse, ExploreResponse, InterviewAnalysisResponse, InterviewGuideResponse,
)
from needs_detector.domain.policies.cpf_evaluator import evaluate_cpf
from needs_detector.infra.llm.base import ManualLLMProvider, MockLLMProvider
from needs_detector.infra.repositories.file_utils import atomic_write, validate_project_path
from needs_detector.infra.scanners.anonymizer import Anonymizer
from needs_detector.domain.policies.question_checker import QuestionChecker


class HumanGateError(Exception):
    pass


def update_status(project_dir: Path, step: str, status: str):
    with open(project_dir / 'project.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    data.setdefault('status', {})[step] = status
    with open(project_dir / 'project.yaml', 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, allow_unicode=True)


def save_ai_completions(project_dir: Path, prompt_used: str, completions: list,
                        job_id=None, fixture=None):
    if not completions:
        return
    dest = project_dir / 'reports' / 'ai_completions.yaml'
    data = {'ai_completions': []}
    if dest.exists():
        with open(dest, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or data
    for item in completions:
        record = dict(item) if isinstance(item, dict) else {'content': str(item)}
        record.update({'step': prompt_used, 'job_id': job_id, 'fixture': fixture})
        data.setdefault('ai_completions', []).append(record)
    with open(dest, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, allow_unicode=True)


def _load_jobs(project_dir: Path):
    path = project_dir / 'manual_prompts' / 'index.yaml'
    if not path.exists():
        return path, []
    with open(path, 'r', encoding='utf-8') as f:
        return path, yaml.safe_load(f) or []


def _save_jobs(path: Path, jobs):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(jobs, f, allow_unicode=True)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _validate_quotes(iv_data, refs, project_dir=None):
    lines, _ = _interview_lines(project_dir, iv_data) if project_dir else (iv_data.get('content', '').splitlines(), None)
    for ref in refs:
        line = ref.get('line')
        quote = ref.get('quote', '')
        if not isinstance(line, int) or line < 1 or line > len(lines):
            raise QuoteValidationError(f'Line {line} out of bounds')
        if quote not in lines[line - 1]:
            raise QuoteValidationError(f"Quote '{quote}' not found in line {line}")


def _validate_ai_completions(completions):
    if completions is None:
        return []
    if not isinstance(completions, list):
        raise ValueError('ai_completions must be a list')
    for item in completions:
        if not isinstance(item, dict):
            raise ValueError('each ai_completion must be an object')
        AICompletion(**item)
    return completions


def _data_classification(project_dir: Path):
    classes = []
    for path in sorted((project_dir / 'interviews').glob('interview_*.yaml')):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                value = (yaml.safe_load(f) or {}).get('data_classification', 'unknown')
        except (OSError, yaml.YAMLError):
            value = 'unknown'
        classes.append(value if value in {'real', 'synthetic'} else 'unknown')
    present = set(classes)
    if len(present) == 1:
        return next(iter(present))
    if len(present) > 1:
        return 'mixed'
    project_file = project_dir / 'project.yaml'
    if project_file.exists():
        with open(project_file, 'r', encoding='utf-8') as f:
            configured = (yaml.safe_load(f) or {}).get('data_classification', 'unknown')
        if configured in {'real', 'synthetic'}:
            return configured
    return 'unknown'


def classification_counts(project_dir: Path):
    counts = {'real': 0, 'synthetic': 0, 'unknown': 0}
    for path in sorted((project_dir / 'interviews').glob('interview_*.yaml')):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                value = (yaml.safe_load(f) or {}).get('data_classification', 'unknown')
        except (OSError, yaml.YAMLError):
            value = 'unknown'
        counts[value if value in counts else 'unknown'] += 1
    if not any(counts.values()):
        try:
            with open(project_dir / 'project.yaml', 'r', encoding='utf-8') as f:
                configured = (yaml.safe_load(f) or {}).get('data_classification', 'unknown')
            if configured in counts and configured != 'unknown':
                counts[configured] = 1
        except (OSError, yaml.YAMLError):
            pass
    return counts


def _reject_source_name(file_name: str):
    if not isinstance(file_name, str) or not file_name.strip():
        raise ValueError('source file_name must be a non-empty string')
    if ntpath.isabs(file_name) or file_name.startswith(('\\\\', '//')):
        raise ValueError(f'absolute source path is not allowed: {file_name}')
    if any(part == '..' for part in Path(file_name).parts):
        raise ValueError(f'source path traversal is not allowed: {file_name}')


def load_source_entries(project_dir: Path):
    index = project_dir / 'sources' / 'index.yaml'
    if not index.exists():
        return []
    with open(index, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or not isinstance(data.get('sources'), list):
        raise ValueError('sources/index.yaml must contain a sources list')
    entries = []
    seen_names = set()
    seen_ids = set()
    for entry in data['sources']:
        if not isinstance(entry, dict):
            raise ValueError('each source entry must be an object')
        file_name = entry.get('file_name')
        _reject_source_name(file_name)
        source_id = entry.get('id')
        if file_name in seen_names or source_id in seen_ids:
            raise ValueError(f'duplicate source entry: {file_name or source_id}')
        seen_names.add(file_name)
        if source_id is not None:
            seen_ids.add(source_id)
        path = project_dir / 'sources' / file_name
        if not _inside_project(path, project_dir):
            raise ValueError(f'source resolves outside project: {file_name}')
        entries.append((entry, path))
    return entries


def _raw_interview_path(project_dir: Path, interview_data):
    source_file = interview_data.get('source_file')
    if not source_file:
        return None
    path = project_dir / source_file
    if not _inside_project(path, project_dir):
        raise ValueError('interview source_file resolves outside project')
    return path


def _interview_lines(project_dir: Path, interview_data):
    raw_path = _raw_interview_path(project_dir, interview_data)
    if raw_path and raw_path.exists():
        return raw_path.read_text(encoding='utf-8').splitlines(), raw_path
    return interview_data.get('content', '').splitlines(), None


def _mark_mock_demo(project_dir: Path):
    path = project_dir / 'project.yaml'
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
    if data.get('data_classification', 'unknown') == 'unknown' and not list((project_dir / 'interviews').glob('interview_*.yaml')):
        data['data_classification'] = 'synthetic'
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, allow_unicode=True)


class ProjectService:
    @staticmethod
    def init_project(target_dir: Path, name: str):
        target_dir = Path(target_dir).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        for name_ in ('sources', 'personas', 'alternatives', 'interviews', 'interviews/raw', 'reports', 'manual_prompts'):
            (target_dir / name_).mkdir(exist_ok=True)
        data = {'id': 'proj_001', 'name': name, 'status': {
            'step1_draw': 'unstarted', 'step2_explore': 'unstarted',
            'step3_listen': 'unstarted', 'step4_learn': 'unstarted'},
            'human_gate_enabled': True, 'data_classification': 'unknown'}
        with open(target_dir / 'project.yaml', 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, allow_unicode=True)
        with open(target_dir / 'sources' / 'index.yaml', 'w', encoding='utf-8') as f:
            yaml.safe_dump({'sources': []}, f)
        with open(target_dir / 'manual_prompts' / 'index.yaml', 'w', encoding='utf-8') as f:
            yaml.safe_dump([], f)

    @staticmethod
    def add_idea(project_dir: Path, file_path: str):
        atomic_write(project_dir / 'idea.md', Path(file_path).read_text(encoding='utf-8'), project_dir)

    @staticmethod
    def add_source(project_dir: Path, file_path: str):
        src = Path(file_path).resolve()
        dest = project_dir / 'sources' / src.name
        validate_project_path(dest, project_dir)
        entries = load_source_entries(project_dir)
        if any(entry.get('file_name') == src.name for entry, _ in entries):
            raise ValueError(f'source already registered: {src.name}')
        shutil.copy(src, dest)
        index = project_dir / 'sources' / 'index.yaml'
        with open(index, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {'sources': []}
        data.setdefault('sources', []).append({'id': f"src_{len(data['sources']) + 1}",
                                                'file_name': src.name, 'type': 'markdown'})
        with open(index, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, allow_unicode=True)

    @staticmethod
    def status(project_dir: Path):
        with open(project_dir / 'project.yaml', 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        print({'status': data.get('status', {}), 'data_classification': _data_classification(project_dir),
               'classification_counts': classification_counts(project_dir)})


def get_llm_provider(provider: str, project_dir: Path):
    if provider == 'manual':
        return ManualLLMProvider(project_dir / 'manual_prompts')
    if provider != 'mock':
        raise ValueError(f'Unknown provider: {provider}')
    return MockLLMProvider()


def parse_and_save_draw(project_dir: Path, content: str, ai_completions: list):
    parsed = json.loads(content)
    DrawResponse(**parsed)
    for persona in parsed['personas']:
        persona['ai_completions'] = ai_completions
        dest = project_dir / 'personas' / f"persona_{persona['id']}.yaml"
        validate_project_path(dest, project_dir)
        with open(dest, 'w', encoding='utf-8') as f:
            yaml.safe_dump(persona, f, allow_unicode=True)
    save_ai_completions(project_dir, 'draw_persona', ai_completions)
    update_status(project_dir, 'step1_draw', 'completed')


def parse_and_save_explore(project_dir: Path, content: str, ai_completions=None):
    parsed = json.loads(content)
    ExploreResponse(**parsed)
    dest = project_dir / 'alternatives' / 'alternatives.yaml'
    validate_project_path(dest, project_dir)
    with open(dest, 'w', encoding='utf-8') as f:
        yaml.safe_dump(parsed, f, allow_unicode=True)
    save_ai_completions(project_dir, 'explore_alternatives', ai_completions or [])
    update_status(project_dir, 'step2_explore', 'completed')


class DrawService:
    @staticmethod
    def draw(project_dir: Path, provider: str, fixture_key=None):
        idea = (project_dir / 'idea.md').read_text(encoding='utf-8') if (project_dir / 'idea.md').exists() else ''
        source_text = ''
        index = project_dir / 'sources' / 'index.yaml'
        if index.exists():
            for src, source_path in load_source_entries(project_dir):
                source_text += '\n---\n' + source_path.read_text(encoding='utf-8')
        resp = get_llm_provider(provider, project_dir).generate(
            'draw_persona', f'Idea:\n{idea}\nSources:\n{source_text}', fixture_key, project_dir)
        if provider == 'manual':
            update_status(project_dir, 'step1_draw', 'waiting_llm')
            print(resp.content)
            return
        parse_and_save_draw(project_dir, resp.content, resp.ai_completions)
        _mark_mock_demo(project_dir)


class ExploreService:
    @staticmethod
    def explore(project_dir: Path, provider: str, fixture_key=None):
        context = '\n'.join(p.read_text(encoding='utf-8') for p in sorted((project_dir / 'personas').glob('*.yaml')))
        resp = get_llm_provider(provider, project_dir).generate('explore_alternatives', context, fixture_key, project_dir)
        if provider == 'manual':
            update_status(project_dir, 'step2_explore', 'waiting_llm')
            print(resp.content)
            return
        parse_and_save_explore(project_dir, resp.content, resp.ai_completions)
        _mark_mock_demo(project_dir)


def _guide_markdown(parsed):
    rows = ['## Interview Guide', '', '### Core Questions']
    for heading in ('core_questions', 'deep_dive_questions'):
        if heading == 'deep_dive_questions':
            rows += ['', '### Deep Dive Questions']
        for question in parsed.get(heading, []):
            check = QuestionChecker.check(question)
            suffix = f" (WARNING: {check['reason']} -> {check['suggestion']})" if check.get('is_warning') else ' (OK)'
            rows.append(f'- {question}{suffix}')
    rows += ['', "### Warning", "Avoid leading questions. Never ask 'Would you use this?'"]
    return '\n'.join(rows)


class InterviewService:
    @staticmethod
    def generate_guide(project_dir: Path, provider='mock', fixture_key=None):
        resp = get_llm_provider(provider, project_dir).generate('interview_guide', 'Generate questions', fixture_key, project_dir)
        if provider == 'manual':
            update_status(project_dir, 'step3_listen', 'waiting_llm')
            print(resp.content)
            return
        parsed = json.loads(resp.content)
        InterviewGuideResponse(**parsed)
        atomic_write(project_dir / 'interviews' / 'guide.md', _guide_markdown(parsed), project_dir)
        save_ai_completions(project_dir, 'interview_guide', resp.ai_completions)
        update_status(project_dir, 'step3_listen', 'in_progress')
        if provider == 'mock':
            _mark_mock_demo(project_dir)

    @staticmethod
    def add_interview(project_dir: Path, file_path: str, data_classification='unknown'):
        raw_bytes = Path(file_path).read_bytes()
        content = raw_bytes.decode('utf-8')
        found = Anonymizer.scan(content)
        if found:
            print(f'Warning: Personal info detected: {found}')
        interview_id = Path(file_path).stem
        dest = project_dir / 'interviews' / f'interview_{interview_id}.yaml'
        raw_dest = project_dir / 'interviews' / 'raw' / f'{interview_id}.md'
        if dest.exists() or raw_dest.exists():
            raise ValueError(f'interview already exists: {interview_id}')
        if data_classification not in {'real', 'synthetic', 'unknown'}:
            raise ValueError('data_classification must be real, synthetic, or unknown')
        validate_project_path(dest, project_dir)
        validate_project_path(raw_dest, project_dir)
        raw_dest.write_bytes(raw_bytes)
        source_file = f'interviews/raw/{interview_id}.md'
        source_hash = hashlib.sha256(raw_bytes).hexdigest()
        with open(dest, 'w', encoding='utf-8') as f:
            yaml.safe_dump({'content': content, 'refutations': [], 'target': interview_id,
                            'data_classification': data_classification,
                            'source_file': source_file, 'source_sha256': source_hash},
                           f, allow_unicode=True)


class LearnService:
    @staticmethod
    def learn(project_dir: Path, provider: str, fixture_key=None):
        interviews = sorted((project_dir / 'interviews').glob('interview_*.yaml'))
        with open(project_dir / 'project.yaml', 'r', encoding='utf-8') as f:
            project = yaml.safe_load(f) or {}
        if project.get('human_gate_enabled', True) and not interviews:
            raise HumanGateError('No interviews found. Cannot proceed to Learn phase.')
        llm = get_llm_provider(provider, project_dir)
        if provider == 'manual':
            generated = []
            for iv in interviews:
                with open(iv, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                resp = llm.generate('learn_interview', f'Target:{iv.stem}\nContent:{data.get("content", "")}', fixture_key, project_dir)
                generated.append(resp.content)
            update_status(project_dir, 'step4_learn', 'waiting_llm')
            print(f'Generated {len(generated)} waiting_llm jobs')
            return

        for iv in interviews:
            with open(iv, 'r', encoding='utf-8') as f:
                iv_data = yaml.safe_load(f) or {}
            resp = llm.generate('learn_interview', iv_data.get('content', ''), fixture_key, project_dir)
            parsed = json.loads(resp.content)
            InterviewAnalysisResponse(**parsed)
            _validate_quotes(iv_data, parsed.get('refutations', []), project_dir)
            iv_data['refutations'] = parsed.get('refutations', [])
            iv_data['cpf_evidence'] = parsed.get('cpf_evidence', {})
            with open(iv, 'w', encoding='utf-8') as f:
                yaml.safe_dump(iv_data, f, allow_unicode=True)
            save_ai_completions(project_dir, 'learn_interview', resp.ai_completions, fixture=resp.fixture_used)
        _finalize_learn(project_dir, interviews)
        _mark_mock_demo(project_dir)


def _finalize_learn(project_dir, interviews):
    cpf = evaluate_cpf(interviews)
    all_content = ''.join(iv.read_text(encoding='utf-8') for iv in interviews)
    result = {'cpf_evaluation': cpf, 'analysis_hash': hashlib.sha256(all_content.encode('utf-8')).hexdigest()[:16]}
    with open(project_dir / 'reports' / 'learn_results.yaml', 'w', encoding='utf-8') as f:
        yaml.safe_dump(result, f, allow_unicode=True)
    update_status(project_dir, 'step3_listen', 'completed')
    update_status(project_dir, 'step4_learn', 'completed')


class ImportService:
    @staticmethod
    def import_response(project_dir: Path, json_file_path: str):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f'Cannot read response JSON: {exc}') from exc
        if not isinstance(data, dict):
            raise ValueError('Response root must be an object')
        prompt = data.get('prompt_used')
        if prompt not in {'draw_persona', 'explore_alternatives', 'interview_guide', 'learn_interview', 'learn_refutations'}:
            raise ValueError(f'Unknown prompt_used: {prompt}')
        content = data.get('content')
        if not isinstance(content, dict):
            raise ValueError('Response content must be an object')
        completions = _validate_ai_completions(data.get('ai_completions', []))
        job_id = data.get('job_id')
        if not isinstance(job_id, str) or not job_id:
            raise ValueError('job_id is required')
        index_file, jobs = _load_jobs(project_dir)
        job = next((j for j in jobs if j.get('job_id') == job_id), None)
        if not job:
            raise ValueError(f'Unregistered job_id: {job_id}')
        if job.get('prompt_used') != prompt:
            raise ValueError('prompt_used does not match registered job')
        if job.get('status') == 'imported':
            raise ValueError(f'Job already imported: {job_id}')
        expected_target = job.get('target')
        if data.get('target') != expected_target:
            raise ValueError('target does not match registered job')

        try:
            if prompt == 'draw_persona':
                DrawResponse(**content)
                parse_and_save_draw(project_dir, json.dumps(content, ensure_ascii=False), completions)
            elif prompt == 'explore_alternatives':
                ExploreResponse(**content)
                parse_and_save_explore(project_dir, json.dumps(content, ensure_ascii=False), completions)
            elif prompt == 'interview_guide':
                InterviewGuideResponse(**content)
                atomic_write(project_dir / 'interviews' / 'guide.md', _guide_markdown(content), project_dir)
                save_ai_completions(project_dir, prompt, completions, job_id)
                update_status(project_dir, 'step3_listen', 'in_progress')
            else:
                InterviewAnalysisResponse(**content)
                iv_path = project_dir / 'interviews' / f'{expected_target}.yaml'
                if not iv_path.exists():
                    raise ValueError(f'Unknown interview target: {expected_target}')
                with open(iv_path, 'r', encoding='utf-8') as f:
                    iv_data = yaml.safe_load(f) or {}
                _validate_quotes(iv_data, content.get('refutations', []), project_dir)
                iv_data['refutations'] = content.get('refutations', [])
                iv_data['cpf_evidence'] = content.get('cpf_evidence', {})
                with open(iv_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(iv_data, f, allow_unicode=True)
                save_ai_completions(project_dir, prompt, completions, job_id)
        except ValidationError as exc:
            raise ValueError(f'Invalid {prompt} response: {exc}') from exc

        response_dest = project_dir / 'manual_prompts' / job_id / 'response.json'
        response_dest.parent.mkdir(parents=True, exist_ok=True)
        with open(response_dest, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        job['status'] = 'imported'
        job['response_file'] = f'{job_id}/response.json'
        job['imported_at'] = _now()
        _save_jobs(index_file, jobs)

        if prompt in {'learn_interview', 'learn_refutations'}:
            learn_jobs = [j for j in jobs if j.get('prompt_used') in {'learn_interview', 'learn_refutations'}]
            pending = [j for j in learn_jobs if j.get('status') != 'imported']
            if pending:
                update_status(project_dir, 'step4_learn', 'waiting_llm')
                print(f'Imported learn response; waiting for {len(pending)} job(s)')
            else:
                interviews = sorted((project_dir / 'interviews').glob('interview_*.yaml'))
                _finalize_learn(project_dir, interviews)
        print(f'Imported {prompt}')


class ReportService:
    @staticmethod
    def generate_report(project_dir: Path):
        data = {i: '(データなし)' for i in range(1, 16)}
        idea = project_dir / 'idea.md'
        if idea.exists():
            data[1] = idea.read_text(encoding='utf-8') or '(データなし)'
        source_index = project_dir / 'sources' / 'index.yaml'
        if source_index.exists():
            with open(source_index, 'r', encoding='utf-8') as f:
                sources = (yaml.safe_load(f) or {}).get('sources', [])
            if sources:
                data[2] = '\n'.join(f"- {s.get('file_name')} ({s.get('type', 'unknown')})" for s in sources)
        personas = sorted((project_dir / 'personas').glob('*.yaml'))
        qtv = []
        if personas:
            fields = {3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: []}
            for path in personas:
                with open(path, 'r', encoding='utf-8') as f:
                    p = yaml.safe_load(f) or {}
                pid = p.get('id', path.stem)
                fields[3].append(f"[{pid}] {p.get('name', '(データなし)')}")
                fields[4].append(f"[{pid}] {p.get('situation', '(データなし)')}")
                jobs = p.get('jobs', {})
                fields[5].append(f"[{pid}] {jobs.get('functional', '(データなし)')}")
                fields[6].append(f"[{pid}] {jobs.get('emotional', '(データなし)')}")
                fields[7].append(f"[{pid}] {jobs.get('social', '(データなし)')}")
                fields[8].append(f"[{pid}] {p.get('impediments', '(データなし)')}")
                fields[9].append(f"[{pid}] {p.get('current_coping', '(データなし)')} / {p.get('dissatisfaction', '(データなし)')}")
                qtv.extend(f'- [{pid}] {q}' for q in p.get('questions_to_verify', []))
            for key, values in fields.items():
                data[key] = '\n'.join(values)
        alternatives = project_dir / 'alternatives' / 'alternatives.yaml'
        if alternatives.exists():
            with open(alternatives, 'r', encoding='utf-8') as f:
                alts = yaml.safe_load(f) or {}
            for key, name in ((10, 'direct_competition'), (11, 'indirect_alternatives'), (12, 'non_consumption')):
                data[key] = '\n'.join(f"- {a.get('name')}: {a.get('problems')}" for a in alts.get(name, [])) or '(データなし)'
        interviews = sorted((project_dir / 'interviews').glob('interview_*.yaml'))
        quotes = []
        for path in interviews:
            with open(path, 'r', encoding='utf-8') as f:
                iv = yaml.safe_load(f) or {}
            source_path = iv.get('source_file') or f'interviews/{path.name}#content'
            for ref in iv.get('refutations', []):
                quotes.append(f"[{source_path}:L{ref.get('line')}] \"{ref.get('quote')}\"")
        data[13] = '\n'.join(quotes) or '(データなし)'
        learn = project_dir / 'reports' / 'learn_results.yaml'
        if learn.exists():
            with open(learn, 'r', encoding='utf-8') as f:
                result = yaml.safe_load(f) or {}
            completions = []
            ac = project_dir / 'reports' / 'ai_completions.yaml'
            if ac.exists():
                with open(ac, 'r', encoding='utf-8') as f:
                    completions = (yaml.safe_load(f) or {}).get('ai_completions', [])
            data[14] = 'CPF評価:\n' + yaml.safe_dump(result.get('cpf_evaluation', {}), allow_unicode=True)
            data[14] += 'AI補完:\n' + (yaml.safe_dump(completions, allow_unicode=True) if completions else '(AI補完なし)')
        data[15] = '\n'.join(qtv) or '(AI仮説に基づく未確認事項なし)'
        if (project_dir / 'project.yaml').exists():
            with open(project_dir / 'project.yaml', 'r', encoding='utf-8') as f:
                statuses = (yaml.safe_load(f) or {}).get('status', {})
            pending = [k for k, v in statuses.items() if v not in {'completed', 'in_progress'}]
            if pending:
                data[15] += '\n待機・未完了ステップ: ' + ', '.join(pending)
        headings = ['初期アイデア', '入力資料と出典', '対象ペルソナ', 'ペルソナが置かれた状況',
                    '機能的ジョブ', '感情的ジョブ', '社会的ジョブ', '阻害要因',
                    '現在の対処方法と不満', '直接競合', '間接代替', '無消費',
                    'インタビューから得た事実と引用', '反証、CPF評価、AI補完部分',
                    '未確認事項と次に確認すべきこと']
        classification = _data_classification(project_dir)
        warning = '' if classification == 'real' else '\n警告: これは機能確認または仮説生成であり、実顧客検証・CPF確立・市場成立を示しません。\n'
        report = (f'# Final Report\n\nデータ区分: {classification}\n分類内訳: {classification_counts(project_dir)}{warning}\n' +
                  ''.join(f'## {i}. {headings[i - 1]}\n{data[i]}\n\n' for i in range(1, 16)))
        atomic_write(project_dir / 'reports' / 'final_report.md', report, project_dir)


def _inside_project(path: Path, project_dir: Path):
    try:
        path.resolve().relative_to(project_dir.resolve())
        return True
    except ValueError:
        return False


class DoctorService:
    @staticmethod
    def diagnose(project_dir: Path):
        result = {'status': 'ok', 'errors': [], 'warnings': [], 'checks': [], 'next_actions': []}

        def check(name, state, detail):
            result['checks'].append({'name': name, 'status': state, 'detail': detail})
            if state == 'error':
                result['errors'].append(f'{name}: {detail}')
            elif state == 'warning':
                result['warnings'].append(f'{name}: {detail}')

        project_file = project_dir / 'project.yaml'
        if not project_file.exists():
            check('project.yaml', 'error', 'project.yaml がありません。initを実行してください')
            result['status'] = 'error'
            result['next_actions'] = ['needs-detector init <name>']
            return result
        try:
            with open(project_file, 'r', encoding='utf-8') as f:
                project = yaml.safe_load(f)
            if not isinstance(project, dict) or not isinstance(project.get('status'), dict):
                raise ValueError('必須キー status がありません')
            check('project.yaml', 'ok', '構文と必須キーは正常です')
        except (OSError, yaml.YAMLError, ValueError) as exc:
            check('project.yaml', 'error', str(exc))
            result['status'] = 'error'
            result['next_actions'] = ['project.yamlを修復してください']
            return result

        source_index = project_dir / 'sources' / 'index.yaml'
        if source_index.exists():
            try:
                entries = load_source_entries(project_dir)
                missing = [str(path) for _, path in entries if not path.exists()]
                if missing:
                    check('sources', 'error', f'missing={missing}')
                else:
                    check('sources', 'ok', f'{len(entries)}件の資料を確認しました')
            except (OSError, yaml.YAMLError, ValueError) as exc:
                check('sources', 'error', str(exc))
        else:
            check('sources', 'warning', 'sources/index.yamlがありません')

        for path in sorted((project_dir / 'personas').glob('*.yaml')):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    from needs_detector.domain.models.llm_models import Persona
                    Persona(**(yaml.safe_load(f) or {}))
            except (OSError, yaml.YAMLError, ValidationError) as exc:
                check(f'persona:{path.name}', 'error', str(exc))
        alternatives = project_dir / 'alternatives' / 'alternatives.yaml'
        if alternatives.exists():
            try:
                with open(alternatives, 'r', encoding='utf-8') as f:
                    ExploreResponse(**(yaml.safe_load(f) or {}))
                check('alternatives', 'ok', 'スキーマは正常です')
            except (OSError, yaml.YAMLError, ValidationError) as exc:
                check('alternatives', 'error', str(exc))

        interviews = sorted((project_dir / 'interviews').glob('interview_*.yaml'))
        for path in interviews:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    interview = yaml.safe_load(f) or {}
                if not isinstance(interview.get('content'), str) or not isinstance(interview.get('refutations', []), list):
                    raise ValueError('contentまたはrefutationsが不正です')
                raw_path = _raw_interview_path(project_dir, interview)
                if not raw_path:
                    check(f'interview:{path.name}', 'warning', 'legacy interview: source_fileがありません')
                else:
                    if not raw_path.exists():
                        raise ValueError(f'raw interview missing: {raw_path}')
                    raw_bytes = raw_path.read_bytes()
                    raw = raw_bytes.decode('utf-8')
                    expected_hash = interview.get('source_sha256')
                    actual_hash = hashlib.sha256(raw_bytes).hexdigest()
                    if expected_hash and expected_hash != actual_hash:
                        raise ValueError('raw interview hash mismatch')
                _validate_quotes(interview, interview.get('refutations', []), project_dir)
            except (OSError, yaml.YAMLError, ValueError, QuoteValidationError) as exc:
                check(f'interview:{path.name}', 'error', str(exc))

        index_file, jobs = _load_jobs(project_dir)
        ids = [j.get('job_id') for j in jobs if isinstance(j, dict)]
        if len(ids) != len(set(ids)):
            check('manual_jobs', 'error', 'job_idが重複しています')
        unknown_targets = []
        job_errors = []
        for job in jobs:
            if not isinstance(job, dict) or not job.get('job_id'):
                job_errors.append('不正なジョブレコード')
                continue
            request = index_file.parent / str(job.get('prompt_file', ''))
            if not _inside_project(request, project_dir) or not request.exists():
                job_errors.append(f"request missing: {job.get('job_id')}")
            else:
                try:
                    with open(request, 'r', encoding='utf-8') as f:
                        request_data = json_module.load(f)
                    if (request_data.get('job_id') != job.get('job_id') or
                            request_data.get('prompt_used') != job.get('prompt_used') or
                            request_data.get('target') != job.get('target')):
                        job_errors.append(f"request mismatch: {job.get('job_id')}")
                except (OSError, json_module.JSONDecodeError, AttributeError):
                    job_errors.append(f"request invalid: {job.get('job_id')}")
            if job.get('status') == 'imported':
                response = index_file.parent / str(job.get('response_file', ''))
                if not response.exists():
                    job_errors.append(f"response missing: {job.get('job_id')}")
            if job.get('target') and not (project_dir / 'interviews' / f"{job['target']}.yaml").exists():
                unknown_targets.append(job['target'])
            if job.get('status') == 'failed':
                job_errors.append(f"failed job: {job.get('job_id')}")
        if job_errors or unknown_targets:
            check('manual_jobs', 'error', f'{job_errors}, unknown_target={unknown_targets}')
        elif jobs:
            waiting = sum(j.get('status') == 'waiting_llm' for j in jobs)
            check('manual_jobs', 'warning' if waiting else 'ok', f'{len(jobs)}件、waiting={waiting}')

        status = project.get('status', {})
        learn_result = project_dir / 'reports' / 'learn_results.yaml'
        if status.get('step4_learn') == 'completed' and not interviews:
            check('learn_state', 'error', 'インタビュー0件なのにStep 4がcompletedです')
        elif status.get('step4_learn') == 'completed' and not learn_result.exists():
            check('learn_state', 'error', 'Step 4 completedですがlearn_results.yamlがありません')
        else:
            check('learn_state', 'ok', 'Step状態と成果物の基本整合性を確認しました')

        ac_file = project_dir / 'reports' / 'ai_completions.yaml'
        if ac_file.exists():
            try:
                with open(ac_file, 'r', encoding='utf-8') as f:
                    completions = (yaml.safe_load(f) or {}).get('ai_completions', [])
                for item in completions:
                    if item.get('step') not in {'draw_persona', 'explore_alternatives', 'interview_guide', 'learn_interview', 'learn_refutations'}:
                        raise ValueError('AI補完の工程が不明です')
                    artifact = item.get('related_artifact')
                    if artifact and not _inside_project(project_dir / artifact, project_dir):
                        raise ValueError('AI補完の成果物がプロジェクト外です')
                    if not item.get('job_id') and not item.get('fixture') and not artifact:
                        raise ValueError('AI補完の参照元がありません')
                check('ai_completions', 'ok', f'{len(completions)}件を確認しました')
            except (OSError, yaml.YAMLError, ValueError, AttributeError) as exc:
                check('ai_completions', 'error', str(exc))

        report = project_dir / 'reports' / 'final_report.md'
        artifacts = [project_file, project_dir / 'idea.md', source_index, alternatives, learn_result, *interviews]
        artifacts += list((project_dir / 'personas').glob('*.yaml'))
        existing = [p for p in artifacts if p.exists()]
        if report.exists() and existing and max(p.stat().st_mtime for p in existing) > report.stat().st_mtime:
            check('report_freshness', 'warning', '最終レポートが成果物より古い可能性があります')
        else:
            check('report_freshness', 'ok', '最終レポートの時刻を確認しました')
        if report.exists():
            citation_errors = []
            report_text = report.read_text(encoding='utf-8')
            for source_name, line_text, quote in re.findall(r'\[([^\]]+):L(\d+)\]\s+"([^"]*)"', report_text):
                if '#content' in source_name:
                    continue
                source_path = project_dir / source_name
                if not _inside_project(source_path, project_dir) or not source_path.exists():
                    citation_errors.append(f'missing citation source: {source_name}')
                    continue
                lines = source_path.read_text(encoding='utf-8').splitlines()
                line_number = int(line_text)
                if line_number < 1 or line_number > len(lines) or quote not in lines[line_number - 1]:
                    citation_errors.append(f'quote mismatch: {source_name}:L{line_text}')
            if citation_errors:
                check('report_citations', 'error', '; '.join(citation_errors))
            else:
                check('report_citations', 'ok', 'レポート引用のファイル・行・本文を確認しました')

        classification = _data_classification(project_dir)
        if classification != 'real':
            check('data_classification', 'warning', f'{classification}: 実顧客検証ではありません')
        else:
            check('data_classification', 'ok', 'realインタビューのみですがCPF確立は断定しません')
        result['data_classification'] = classification
        result['classification_counts'] = classification_counts(project_dir)
        result['status'] = 'error' if result['errors'] else 'warning' if result['warnings'] else 'ok'
        result['next_actions'] = ['doctorのerrorを修復'] if result['errors'] else []
        return result

    @staticmethod
    def run(project_dir: Path, as_json=False):
        result = DoctorService.diagnose(project_dir)
        if as_json:
            print(json_module.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"doctor: {result['status']}")
            for item in result['errors'] + result['warnings']:
                print(f'- {item}')
            for action in result['next_actions']:
                print(f'次の操作: {action}')
        return 1 if result['errors'] else 0


class NextService:
    @staticmethod
    def suggest(project_dir: Path):
        diagnosis = DoctorService.diagnose(project_dir)
        actions = []
        if diagnosis['errors']:
            actions.append('needs-detector doctor')
            return {'status': diagnosis['status'], 'data_classification': _data_classification(project_dir),
                    'classification_counts': classification_counts(project_dir), 'actions': actions[:3]}
        project_file = project_dir / 'project.yaml'
        if not project_file.exists():
            return {'status': 'error', 'data_classification': 'unknown', 'actions': ['needs-detector init <name>']}
        with open(project_file, 'r', encoding='utf-8') as f:
            project = yaml.safe_load(f) or {}
        if not (project_dir / 'idea.md').exists():
            actions.append('needs-detector add-idea <file>')
        try:
            source_entries = load_source_entries(project_dir)
        except (OSError, yaml.YAMLError, ValueError):
            source_entries = []
        if not source_entries:
            actions.append('needs-detector add-source <file>')
        jobs = _load_jobs(project_dir)[1]
        for job in jobs:
            if job.get('status') == 'waiting_llm':
                actions.append(f"needs-detector import-llm-response <response.json>  # job_id={job.get('job_id')} target={job.get('target')}")
        statuses = project.get('status', {})
        if statuses.get('step1_draw') == 'unstarted' and not actions:
            actions.append('needs-detector draw --provider mock --fixture-key dataset_a')
        if statuses.get('step2_explore') == 'unstarted' and list((project_dir / 'personas').glob('*.yaml')) and len(actions) < 3:
            actions.append('needs-detector explore --provider mock --fixture-key dataset_a')
        if not (project_dir / 'interviews' / 'guide.md').exists() and len(actions) < 3:
            actions.append('needs-detector interview-guide')
        interviews = list((project_dir / 'interviews').glob('interview_*.yaml'))
        if not interviews and len(actions) < 3:
            actions.append('現実の顧客へインタビューし、匿名化記録をadd-interviewする（検証完了とは扱いません）')
        report = project_dir / 'reports' / 'final_report.md'
        artifacts = [project_file, project_dir / 'idea.md', project_dir / 'sources' / 'index.yaml',
                     project_dir / 'alternatives' / 'alternatives.yaml', project_dir / 'reports' / 'learn_results.yaml']
        artifacts += list((project_dir / 'personas').glob('*.yaml'))
        artifacts += list((project_dir / 'interviews').glob('interview_*.yaml'))
        latest = max((path.stat().st_mtime for path in artifacts if path.exists()), default=0)
        if statuses.get('step4_learn') == 'completed' and (not report.exists() or report.stat().st_mtime < latest) and len(actions) < 3:
            actions.append('needs-detector report')
        if not actions:
            actions = ['新しいインタビューを追加する', '未確認事項を検証する']
        return {'status': diagnosis['status'], 'data_classification': _data_classification(project_dir),
                'classification_counts': classification_counts(project_dir), 'actions': actions[:3]}

    @staticmethod
    def run(project_dir: Path, as_json=False):
        result = NextService.suggest(project_dir)
        if as_json:
            print(json_module.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"next ({result['data_classification']}):")
            for action in result['actions']:
                print(f'- {action}')
        return 0
