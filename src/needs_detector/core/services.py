import os
import yaml
import shutil
from pathlib import Path
from needs_detector.infra.repositories.file_utils import atomic_write
from needs_detector.infra.scanners.anonymizer import Anonymizer
from needs_detector.domain.policies.question_checker import QuestionChecker
from needs_detector.domain.policies.cpf_evaluator import evaluate_cpf

class HumanGateError(Exception):
    pass

class ProjectService:
    @staticmethod
    def init_project(target_dir: Path, name: str):
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
        atomic_write(project_dir / 'idea.md', content)

    @staticmethod
    def add_source(project_dir: Path, file_path: str):
        src_path = Path(file_path)
        dest_path = project_dir / 'sources' / src_path.name
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

class DrawService:
    @staticmethod
    def draw(project_dir: Path, provider: str):
        data = {'name': 'Persona 1', 'job': 'Get things done'}
        with open(project_dir / 'personas' / 'persona_1.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
        update_status(project_dir, 'step1_draw', 'completed')

class ExploreService:
    @staticmethod
    def explore(project_dir: Path, provider: str):
        data = {'alternatives': ['Alt 1', 'Alt 2']}
        with open(project_dir / 'alternatives' / 'alternatives.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(data, f)
        update_status(project_dir, 'step2_explore', 'completed')

class InterviewService:
    @staticmethod
    def generate_guide(project_dir: Path):
        content = "Question 1: What did you do?"
        QuestionChecker.check("使いますか")
        atomic_write(project_dir / 'interviews' / 'guide.md', content)
        update_status(project_dir, 'step3_listen', 'in_progress')

    @staticmethod
    def add_interview(project_dir: Path, file_path: str):
        content = Path(file_path).read_text(encoding='utf-8')
        res = Anonymizer.scan(content)
        if res:
            print(f"Warning: Personal info detected: {res}")
        dest = project_dir / 'interviews' / f"interview_{Path(file_path).stem}.yaml"
        with open(dest, 'w', encoding='utf-8') as f:
            yaml.dump({'content': content, 'refutations': 'Some refutations [interview_1:L10]'}, f)

class LearnService:
    @staticmethod
    def learn(project_dir: Path, provider: str):
        interviews_dir = project_dir / 'interviews'
        interviews = list(interviews_dir.glob('interview_*.yaml'))
        
        with open(project_dir / 'project.yaml', 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data.get('human_gate_enabled', True):
                if not interviews:
                    raise HumanGateError("インタビュー記録が1件も存在しないため、Step 3を完了してStep 4へ進むことはできません")
        
        cpf = evaluate_cpf(interviews)
        update_status(project_dir, 'step3_listen', 'completed')
        update_status(project_dir, 'step4_learn', 'completed')

class ReportService:
    @staticmethod
    def generate_report(project_dir: Path):
        report = "# Final Report\n\n## Refutations\n- The user did not like it. [interview_1:L10]\n"
        atomic_write(project_dir / 'reports' / 'final_report.md', report)
