import hashlib
import json
import shutil
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


def _validate_quotes(iv_data, refs):
    lines = iv_data.get('content', '').splitlines()
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


class ProjectService:
    @staticmethod
    def init_project(target_dir: Path, name: str):
        target_dir = Path(target_dir).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        for name_ in ('sources', 'personas', 'alternatives', 'interviews', 'reports', 'manual_prompts'):
            (target_dir / name_).mkdir(exist_ok=True)
        data = {'id': 'proj_001', 'name': name, 'status': {
            'step1_draw': 'unstarted', 'step2_explore': 'unstarted',
            'step3_listen': 'unstarted', 'step4_learn': 'unstarted'},
            'human_gate_enabled': True}
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
            print(yaml.safe_load(f).get('status', {}))


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
            with open(index, 'r', encoding='utf-8') as f:
                for src in (yaml.safe_load(f) or {}).get('sources', []):
                    source_text += '\n---\n' + (project_dir / 'sources' / src['file_name']).read_text(encoding='utf-8')
        resp = get_llm_provider(provider, project_dir).generate(
            'draw_persona', f'Idea:\n{idea}\nSources:\n{source_text}', fixture_key, project_dir)
        if provider == 'manual':
            update_status(project_dir, 'step1_draw', 'waiting_llm')
            print(resp.content)
            return
        parse_and_save_draw(project_dir, resp.content, resp.ai_completions)


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

    @staticmethod
    def add_interview(project_dir: Path, file_path: str):
        content = Path(file_path).read_text(encoding='utf-8')
        found = Anonymizer.scan(content)
        if found:
            print(f'Warning: Personal info detected: {found}')
        dest = project_dir / 'interviews' / f'interview_{Path(file_path).stem}.yaml'
        validate_project_path(dest, project_dir)
        with open(dest, 'w', encoding='utf-8') as f:
            yaml.safe_dump({'content': content, 'refutations': [], 'target': Path(file_path).stem}, f, allow_unicode=True)


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
            _validate_quotes(iv_data, parsed.get('refutations', []))
            iv_data['refutations'] = parsed.get('refutations', [])
            iv_data['cpf_evidence'] = parsed.get('cpf_evidence', {})
            with open(iv, 'w', encoding='utf-8') as f:
                yaml.safe_dump(iv_data, f, allow_unicode=True)
            save_ai_completions(project_dir, 'learn_interview', resp.ai_completions, fixture=resp.fixture_used)
        _finalize_learn(project_dir, interviews)


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
                _validate_quotes(iv_data, content.get('refutations', []))
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
            for ref in iv.get('refutations', []):
                quotes.append(f"[{path.stem}.md:L{ref.get('line')}] \"{ref.get('quote')}\"")
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
        report = '# Final Report\n\n' + ''.join(f'## {i}. {headings[i - 1]}\n{data[i]}\n\n' for i in range(1, 16))
        atomic_write(project_dir / 'reports' / 'final_report.md', report, project_dir)
