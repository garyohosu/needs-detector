import os
import yaml
import shutil
import hashlib
import json
import sys
from pathlib import Path
from needs_detector.infra.repositories.file_utils import atomic_write, validate_project_path
from needs_detector.infra.scanners.anonymizer import Anonymizer
from needs_detector.domain.policies.question_checker import QuestionChecker
from needs_detector.domain.policies.cpf_evaluator import evaluate_cpf
from needs_detector.infra.llm.base import MockLLMProvider, ManualLLMProvider
from needs_detector.domain.models.exceptions import QuoteValidationError

class HumanGateError(Exception):
    pass

class ProjectService:
    @staticmethod
    def init_project(target_dir: Path, name: str):
        target_dir = Path(target_dir).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / 'sources').mkdir(exist_ok=True)
        (target_dir / 'personas').mkdir(exist_ok=True)
        (target_dir / 'alternatives').mkdir(exist_ok=True)
        (target_dir / 'interviews').mkdir(exist_ok=True)
        (target_dir / 'reports').mkdir(exist_ok=True)
        
        proj_data = {
            'id': 'proj_001',
            'name': name,
            'status': {
                'step1_draw': 'unstarted',
                'step2_explore': 'unstarted',
                'step3_listen': 'unstarted',
                'step4_learn': 'unstarted'
            },
            'human_gate_enabled': True
        }
        with open(target_dir / 'project.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(proj_data, f)
        
        with open(target_dir / 'sources' / 'index.yaml', 'w', encoding='utf-8') as f:
            yaml.dump({'sources': []}, f)

    @staticmethod
    def add_idea(project_dir: Path, file_path: str):
        content = Path(file_path).read_text(encoding='utf-8')
        atomic_write(project_dir / 'idea.md', content, project_dir)

    @staticmethod
    def add_source(project_dir: Path, file_path: str):
        src_path = Path(file_path).resolve()
        dest_path = project_dir / 'sources' / src_path.name
        validate_project_path(dest_path, project_dir)
        shutil.copy(src_path, dest_path)
        
        index_file = project_dir / 'sources' / 'index.yaml'
        with open(index_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {'sources': []}
        data['sources'].append({
            'id': f"src_{len(data['sources'])+1}",
            'file_name': src_path.name,
            'type': 'markdown'
        })
        with open(index_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f)

    @staticmethod
    def status(project_dir: Path):
        with open(project_dir / 'project.yaml', 'r', encoding='utf-8') as f:
            print(yaml.safe_load(f)['status'])

def update_status(project_dir: Path, step: str, status: str):
    proj_file = project_dir / 'project.yaml'
    with open(proj_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    data['status'][step] = status
    with open(proj_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)

def get_llm_provider(provider: str, project_dir: Path):
    if provider == 'manual':
        return ManualLLMProvider(project_dir / 'exports')
    return MockLLMProvider()

def parse_and_save_draw(project_dir: Path, content: str, ai_completions: list):
    parsed = json.loads(content)
    for persona in parsed.get("personas", []):
        persona['ai_completions'] = ai_completions
        dest = project_dir / 'personas' / f"persona_{persona.get('id', 'default')}.yaml"
        validate_project_path(dest, project_dir)
        with open(dest, 'w', encoding='utf-8') as f:
            yaml.dump(persona, f, allow_unicode=True)
    update_status(project_dir, 'step1_draw', 'completed')

def parse_and_save_explore(project_dir: Path, content: str):
    parsed = json.loads(content)
    dest = project_dir / 'alternatives' / 'alternatives.yaml'
    validate_project_path(dest, project_dir)
    with open(dest, 'w', encoding='utf-8') as f:
        yaml.dump(parsed, f, allow_unicode=True)
    update_status(project_dir, 'step2_explore', 'completed')

class DrawService:
    @staticmethod
    def draw(project_dir: Path, provider: str):
        idea = ""
        idea_path = project_dir / 'idea.md'
        if idea_path.exists():
            idea = idea_path.read_text(encoding='utf-8')
        
        sources = ""
        index_file = project_dir / 'sources' / 'index.yaml'
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {'sources': []}
                for src in data.get('sources', []):
                    src_content = (project_dir / 'sources' / src['file_name']).read_text(encoding='utf-8')
                    sources += f"\n---\n{src_content}"
        
        context = f"Idea:\n{idea}\nSources:\n{sources}"
        llm = get_llm_provider(provider, project_dir)
        resp = llm.generate('draw_persona', context)
        
        if resp.content.startswith('Exported to'):
            print(resp.content)
            return

        parse_and_save_draw(project_dir, resp.content, resp.ai_completions)

class ExploreService:
    @staticmethod
    def explore(project_dir: Path, provider: str):
        personas = list((project_dir / 'personas').glob('*.yaml'))
        context = ""
        for p in personas:
            context += p.read_text(encoding='utf-8')
            
        llm = get_llm_provider(provider, project_dir)
        resp = llm.generate('explore_alternatives', context)
        
        if resp.content.startswith('Exported to'):
            print(resp.content)
            return

        parse_and_save_explore(project_dir, resp.content)

class InterviewService:
    @staticmethod
    def generate_guide(project_dir: Path, provider: str = 'mock'):
        llm = get_llm_provider(provider, project_dir)
        resp = llm.generate('interview_guide', "Generate questions")
        
        if resp.content.startswith('Exported to'):
            print(resp.content)
            return

        parsed = json.loads(resp.content)
        content = "## Interview Guide\n\n### Core Questions\n"
        for q in parsed.get("core_questions", []):
            chk = QuestionChecker.check(q)
            if chk.get('is_warning'):
                content += f"- {q} (WARNING: {chk.get('reason')} -> {chk.get('suggestion')})\n"
            else:
                content += f"- {q} (OK)\n"
        content += "\n### Deep Dive Questions\n"
        for q in parsed.get("deep_dive_questions", []):
            chk = QuestionChecker.check(q)
            if chk.get('is_warning'):
                content += f"- {q} (WARNING: {chk.get('reason')} -> {chk.get('suggestion')})\n"
            else:
                content += f"- {q} (OK)\n"
            
        content += "\n### Warning\nAvoid leading questions. Never ask 'Would you use this?'"
        
        dest = project_dir / 'interviews' / 'guide.md'
        atomic_write(dest, content, project_dir)
        update_status(project_dir, 'step3_listen', 'in_progress')

    @staticmethod
    def add_interview(project_dir: Path, file_path: str):
        content = Path(file_path).read_text(encoding='utf-8')
        res = Anonymizer.scan(content)
        if res:
            print(f"Warning: Personal info detected: {res}")
            
        dest = project_dir / 'interviews' / f"interview_{Path(file_path).stem}.yaml"
        validate_project_path(dest, project_dir)
        
        with open(dest, 'w', encoding='utf-8') as f:
            yaml.dump({'content': content, 'refutations': []}, f, allow_unicode=True)

class LearnService:
    @staticmethod
    def learn(project_dir: Path, provider: str):
        interviews_dir = project_dir / 'interviews'
        interviews = list(interviews_dir.glob('interview_*.yaml'))
        
        with open(project_dir / 'project.yaml', 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data.get('human_gate_enabled', True):
                if not interviews:
                    raise HumanGateError("No interviews found. Cannot proceed to Learn phase.")
        
        llm = get_llm_provider(provider, project_dir)
        
        for iv in interviews:
            with open(iv, 'r', encoding='utf-8') as f:
                iv_data = yaml.safe_load(f)
                
            iv_lines = iv_data['content'].splitlines()
            resp = llm.generate('learn_refutations', iv_data['content'])
            if not resp.content.startswith('Exported to'):
                parsed = json.loads(resp.content)
                refs = parsed.get("refutations", [])
                
                for r in refs:
                    q_text = r.get('quote', '')
                    line_num = r.get('line', 0)
                    if line_num < 1 or line_num > len(iv_lines):
                        raise QuoteValidationError(f"Line {line_num} out of bounds")
                    if q_text not in iv_lines[line_num - 1]:
                        raise QuoteValidationError(f"Quote '{q_text}' not found in line {line_num}")
                
                iv_data['refutations'] = refs
                with open(iv, 'w', encoding='utf-8') as f:
                    yaml.dump(iv_data, f, allow_unicode=True)
        
        cpf = evaluate_cpf(interviews)
        
        learn_data = {'cpf_evaluation': cpf, 'analysis_hash': 'mock_hash'}
        dest = project_dir / 'reports' / 'learn_results.yaml'
        validate_project_path(dest, project_dir)
        with open(dest, 'w', encoding='utf-8') as f:
            yaml.dump(learn_data, f, allow_unicode=True)
            
        update_status(project_dir, 'step3_listen', 'completed')
        update_status(project_dir, 'step4_learn', 'completed')

class ImportService:
    @staticmethod
    def import_response(project_dir: Path, json_file_path: str):
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        prompt_used = data.get('prompt_used', '')
        content = json.dumps(data.get('content', {}))
        
        if prompt_used == 'draw_persona':
            parse_and_save_draw(project_dir, content, data.get('ai_completions', []))
            print("Imported draw persona")
        elif prompt_used == 'explore_alternatives':
            parse_and_save_explore(project_dir, content)
            print("Imported explore alternatives")
        elif prompt_used == 'interview_guide':
            print("Imported interview guide")
        elif prompt_used in ('learn_refutations', 'learn_interview'):
            print("Imported learn interview")
        else:
            print("Unknown prompt used in import")
            sys.exit(1)

class ReportService:
    @staticmethod
    def generate_report(project_dir: Path):
        report_data = {f"Section {i}": "未確認" for i in range(1, 16)}
        
        idea = ""
        if (project_dir / 'idea.md').exists():
            idea = (project_dir / 'idea.md').read_text(encoding='utf-8')
            report_data["Section 1"] = idea if idea else "未確認"

        report = "# Final Report\n\n"
        for i in range(1, 16):
            report += f"## Section {i}\n{report_data[f'Section {i}']}\n\n"
            
        atomic_write(project_dir / 'reports' / 'final_report.md', report, project_dir)
