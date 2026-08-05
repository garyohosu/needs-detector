import os
import yaml
import shutil
import hashlib
import json
from pathlib import Path
from needs_detector.infra.repositories.file_utils import atomic_write, validate_project_path
from needs_detector.infra.scanners.anonymizer import Anonymizer
from needs_detector.domain.policies.question_checker import QuestionChecker
from needs_detector.domain.policies.cpf_evaluator import evaluate_cpf
from needs_detector.infra.llm.base import MockLLMProvider, ManualLLMProvider

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

def parse_and_save_explore(project_dir: Path, content: str):
    parsed = json.loads(content)
    dest = project_dir / 'alternatives' / 'alternatives.yaml'
    validate_project_path(dest, project_dir)
    with open(dest, 'w', encoding='utf-8') as f:
        yaml.dump(parsed, f, allow_unicode=True)
    update_status(project_dir, 'step2_explore', 'completed')

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
            content += f"- {q}\n"
        content += "\n### Deep Dive Questions\n"
        for q in parsed.get("deep_dive_questions", []):
            content += f"- {q}\n"
            
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
        
        # We save raw text first, refutations filled in learn
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
            resp = llm.generate('learn_refutations', iv_data['content'])
            if not resp.content.startswith('Exported to'):
                parsed = json.loads(resp.content)
                iv_data['refutations'] = parsed.get("refutations", [])
                with open(iv, 'w', encoding='utf-8') as f:
                    yaml.dump(iv_data, f, allow_unicode=True)
        
        cpf = evaluate_cpf(interviews)
        
        learn_data = {'cpf_evaluation': cpf, 'analysis_hash': hashlib.md5(str(interviews).encode()).hexdigest()[:6]}
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
        else:
            print("Unknown prompt used in import")

class ReportService:
    @staticmethod
    def generate_report(project_dir: Path):
        # Initial idea
        idea = ""
        if (project_dir / 'idea.md').exists():
            idea = (project_dir / 'idea.md').read_text(encoding='utf-8')
            
        # Personas
        personas = []
        for p in (project_dir / 'personas').glob('*.yaml'):
            with open(p, 'r', encoding='utf-8') as f:
                personas.append(yaml.safe_load(f))
                
        persona_str = ""
        for p in personas:
            persona_str += f"- Name: {p.get('name')}, Situation: {p.get('situation')}\n"
            jobs = p.get('jobs', {})
            persona_str += f"  - Functional: {jobs.get('functional')}\n"
            persona_str += f"  - Emotional: {jobs.get('emotional')}\n"
            persona_str += f"  - Social: {jobs.get('social')}\n"
            persona_str += f"  - Impediments: {p.get('impediments')}\n"
            
        # Alternatives
        alts = {}
        alt_path = project_dir / 'alternatives' / 'alternatives.yaml'
        if alt_path.exists():
            with open(alt_path, 'r', encoding='utf-8') as f:
                alts = yaml.safe_load(f) or {}
                
        alts_str = "Direct:\n"
        for a in alts.get('direct_competition', []):
            alts_str += f"- {a.get('name')}: {a.get('benefits')} / {a.get('problems')} / {a.get('cost_time')}\n"
        alts_str += "Indirect:\n"
        for a in alts.get('indirect_alternatives', []):
            alts_str += f"- {a.get('name')}: {a.get('benefits')} / {a.get('problems')} / {a.get('cost_time')}\n"
        alts_str += "Non-Consumption:\n"
        for a in alts.get('non_consumption', []):
            alts_str += f"- {a.get('name')}: {a.get('benefits')} / {a.get('problems')} / {a.get('cost_time')}\n"
            
        # Refutations & Learn
        learn_file = project_dir / 'reports' / 'learn_results.yaml'
        learn_data = {}
        if learn_file.exists():
            with open(learn_file, 'r', encoding='utf-8') as f:
                learn_data = yaml.safe_load(f)
            
        interviews = list((project_dir / 'interviews').glob('interview_*.yaml'))
        refutations_text = ""
        for iv in interviews:
            with open(iv, 'r', encoding='utf-8') as f:
                iv_data = yaml.safe_load(f)
            refs = iv_data.get('refutations', [])
            for r in refs:
                refutations_text += f"- {r['quote']} [{iv.stem}.md:L{r.get('line')}]\n"
                
        cpf_eval = learn_data.get('cpf_evaluation', {})
        cpf_text = f"- Real Problem: {cpf_eval.get('real_problem', '未確認')}\n" \
                   f"- First Mover: {cpf_eval.get('first_mover', '未確認')}\n" \
                   f"- Current Alternative: {cpf_eval.get('current_alternative', '未確認')}\n"
                   
        report = f"# Final Report\n\n## Initial Idea\n{idea}\n\n## Personas & Situations\n{persona_str}\n\n## Problem Hypotheses & Alternatives\n{alts_str}\n\n## CPF Evaluation\n{cpf_text}\n\n## Refutations\n{refutations_text}\n"
        atomic_write(project_dir / 'reports' / 'final_report.md', report, project_dir)

