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
from needs_detector.domain.models.llm_models import DrawResponse, ExploreResponse, InterviewGuideResponse, InterviewAnalysisResponse
from pydantic import ValidationError

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
        return ManualLLMProvider(project_dir / 'manual_prompts')
    return MockLLMProvider()

def parse_and_save_draw(project_dir: Path, content: str, ai_completions: list):
    parsed = json.loads(content)
    DrawResponse(**parsed)
    for persona in parsed.get("personas", []):
        persona['ai_completions'] = ai_completions
        dest = project_dir / 'personas' / f"persona_{persona.get('id', 'default')}.yaml"
        validate_project_path(dest, project_dir)
        with open(dest, 'w', encoding='utf-8') as f:
            yaml.dump(persona, f, allow_unicode=True)
    update_status(project_dir, 'step1_draw', 'completed')

def parse_and_save_explore(project_dir: Path, content: str):
    parsed = json.loads(content)
    ExploreResponse(**parsed)
    dest = project_dir / 'alternatives' / 'alternatives.yaml'
    validate_project_path(dest, project_dir)
    with open(dest, 'w', encoding='utf-8') as f:
        yaml.dump(parsed, f, allow_unicode=True)
    update_status(project_dir, 'step2_explore', 'completed')

class DrawService:
    @staticmethod
    def draw(project_dir: Path, provider: str, fixture_key: str = None):
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
        resp = llm.generate('draw_persona', context, fixture_key, project_dir)
        
        if provider == 'manual':
            update_status(project_dir, 'step1_draw', 'waiting_llm')
            print(resp.content)
            return

        parse_and_save_draw(project_dir, resp.content, resp.ai_completions)

class ExploreService:
    @staticmethod
    def explore(project_dir: Path, provider: str, fixture_key: str = None):
        personas = list((project_dir / 'personas').glob('*.yaml'))
        context = ""
        for p in personas:
            context += p.read_text(encoding='utf-8')
            
        llm = get_llm_provider(provider, project_dir)
        resp = llm.generate('explore_alternatives', context, fixture_key, project_dir)
        
        if provider == 'manual':
            update_status(project_dir, 'step2_explore', 'waiting_llm')
            print(resp.content)
            return

        parse_and_save_explore(project_dir, resp.content)

class InterviewService:
    @staticmethod
    def generate_guide(project_dir: Path, provider: str = 'mock', fixture_key: str = None):
        llm = get_llm_provider(provider, project_dir)
        resp = llm.generate('interview_guide', "Generate questions", fixture_key, project_dir)
        
        if provider == 'manual':
            update_status(project_dir, 'step3_listen', 'waiting_llm')
            print(resp.content)
            return

        parsed = json.loads(resp.content)
        InterviewGuideResponse(**parsed)
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
            yaml.dump({'content': content, 'refutations': [], 'target': Path(file_path).stem}, f, allow_unicode=True)

class LearnService:
    @staticmethod
    def learn(project_dir: Path, provider: str, fixture_key: str = None):
        interviews_dir = project_dir / 'interviews'
        interviews = list(interviews_dir.glob('interview_*.yaml'))
        
        with open(project_dir / 'project.yaml', 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data.get('human_gate_enabled', True):
                if not interviews:
                    raise HumanGateError("No interviews found. Cannot proceed to Learn phase.")
        
        llm = get_llm_provider(provider, project_dir)
        
        if provider == 'manual':
            for iv in interviews:
                with open(iv, 'r', encoding='utf-8') as f:
                    iv_data = yaml.safe_load(f)
                resp = llm.generate(f'learn_interview', f"Target:{iv.stem}\nContent:{iv_data['content']}", fixture_key, project_dir)
            update_status(project_dir, 'step4_learn', 'waiting_llm')
            return

        for iv in interviews:
            with open(iv, 'r', encoding='utf-8') as f:
                iv_data = yaml.safe_load(f)
                
            iv_lines = iv_data['content'].splitlines()
            resp = llm.generate('learn_interview', iv_data['content'], fixture_key, project_dir)
            parsed = json.loads(resp.content)
            InterviewAnalysisResponse(**parsed)
            refs = parsed.get("refutations", [])
            cpf_evidence = parsed.get("cpf_evidence", {})
            
            for r in refs:
                q_text = r.get('quote', '')
                line_num = r.get('line', 0)
                if line_num < 1 or line_num > len(iv_lines):
                    raise QuoteValidationError(f"Line {line_num} out of bounds")
                if q_text not in iv_lines[line_num - 1]:
                    raise QuoteValidationError(f"Quote '{q_text}' not found in line {line_num}")
            
            iv_data['refutations'] = refs
            iv_data['cpf_evidence'] = cpf_evidence
            with open(iv, 'w', encoding='utf-8') as f:
                yaml.dump(iv_data, f, allow_unicode=True)
        
        cpf = evaluate_cpf(interviews)
        
        all_content = "".join([iv.read_text(encoding='utf-8') for iv in interviews])
        analysis_hash = hashlib.sha256(all_content.encode('utf-8')).hexdigest()[:16]
        
        learn_data = {'cpf_evaluation': cpf, 'analysis_hash': analysis_hash}
        dest = project_dir / 'reports' / 'learn_results.yaml'
        validate_project_path(dest, project_dir)
        with open(dest, 'w', encoding='utf-8') as f:
            yaml.dump(learn_data, f, allow_unicode=True)
            
        update_status(project_dir, 'step3_listen', 'completed')
        update_status(project_dir, 'step4_learn', 'completed')

class ImportService:
    @staticmethod
    def import_response(project_dir: Path, json_file_path: str):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            sys.exit(1)
            
        import yaml
        ac_file = project_dir / 'reports' / 'ai_completions.yaml'
        if not ac_file.exists():
            with open(ac_file, 'w', encoding='utf-8') as f:
                yaml.dump({'ai_completions': []}, f)
                
        ai_completions = data.get('ai_completions', [])
        if ai_completions:
            with open(ac_file, 'r', encoding='utf-8') as f:
                ac_data = yaml.safe_load(f) or {'ai_completions': []}
            for ac in ai_completions:
                if isinstance(ac, dict):
                    ac['step'] = data.get('prompt_used')
                    ac['job_id'] = data.get('job_id')
                    ac_data['ai_completions'].append(ac)
                elif isinstance(ac, str):
                    ac_data['ai_completions'].append({
                        'step': data.get('prompt_used'),
                        'job_id': data.get('job_id'),
                        'content': ac
                    })
            with open(ac_file, 'w', encoding='utf-8') as f:
                yaml.dump(ac_data, f, allow_unicode=True)

        prompt_used = data.get('prompt_used', '')
        content_dict = data.get('content', {})
        if not prompt_used or not content_dict:
            sys.exit(1)

        job_id = data.get('job_id')
        job_record = None
        index_file = project_dir / 'manual_prompts' / 'index.yaml'
        if job_id and index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                jobs = yaml.safe_load(f) or []
            for j in jobs:
                if j.get('job_id') == job_id:
                    job_record = j
                    break
            if not job_record or job_record.get('prompt_used') != prompt_used:
                sys.exit(1)
            target = job_record.get('target')
            if prompt_used == 'learn_interview' and target and data.get('target') != target:
                sys.exit(1)

        content = json.dumps(content_dict)
        
        try:
            if prompt_used == 'draw_persona':
                DrawResponse(**content_dict)
                parse_and_save_draw(project_dir, content, data.get('ai_completions', []))
                print("Imported draw persona")
            elif prompt_used == 'explore_alternatives':
                ExploreResponse(**content_dict)
                parse_and_save_explore(project_dir, content)
                print("Imported explore alternatives")
            elif prompt_used == 'interview_guide':
                InterviewGuideResponse(**content_dict)
                parsed = content_dict
                guide_content = "## Interview Guide\n\n### Core Questions\n"
                for q in parsed.get("core_questions", []):
                    chk = QuestionChecker.check(q)
                    if chk.get('is_warning'):
                        guide_content += f"- {q} (WARNING: {chk.get('reason')} -> {chk.get('suggestion')})\n"
                    else:
                        guide_content += f"- {q} (OK)\n"
                guide_content += "\n### Deep Dive Questions\n"
                for q in parsed.get("deep_dive_questions", []):
                    chk = QuestionChecker.check(q)
                    if chk.get('is_warning'):
                        guide_content += f"- {q} (WARNING: {chk.get('reason')} -> {chk.get('suggestion')})\n"
                    else:
                        guide_content += f"- {q} (OK)\n"
                    
                guide_content += "\n### Warning\nAvoid leading questions. Never ask 'Would you use this?'"
                
                dest = project_dir / 'interviews' / 'guide.md'
                atomic_write(dest, guide_content, project_dir)
                update_status(project_dir, 'step3_listen', 'in_progress')
                print("Imported interview guide")
            elif prompt_used in ('learn_refutations', 'learn_interview'):
                InterviewAnalysisResponse(**content_dict)
                target = data.get('target')
                if not target:
                    sys.exit(1)
                iv_path = project_dir / 'interviews' / f"{target}.yaml"
                if not iv_path.exists():
                    sys.exit(1)
                
                with open(iv_path, 'r', encoding='utf-8') as f:
                    iv_data = yaml.safe_load(f)
                iv_lines = iv_data['content'].splitlines()
                refs = content_dict.get("refutations", [])
                cpf_evidence = content_dict.get("cpf_evidence", {})
                for r in refs:
                    q_text = r.get('quote', '')
                    line_num = r.get('line', 0)
                    if not isinstance(line_num, int):
                        sys.exit(1)
                    if line_num < 1 or line_num > len(iv_lines):
                        sys.exit(1)
                    if q_text not in iv_lines[line_num - 1]:
                        sys.exit(1)
                iv_data['refutations'] = refs
                iv_data['cpf_evidence'] = cpf_evidence
                with open(iv_path, 'w', encoding='utf-8') as f:
                    yaml.dump(iv_data, f, allow_unicode=True)
                
                all_completed = True
                if job_record and index_file.exists():
                    job_record['status'] = 'imported'
                    from datetime import datetime, timezone
                    job_record['imported_at'] = datetime.now(timezone.utc).isoformat()
                    with open(index_file, 'w', encoding='utf-8') as f:
                        yaml.dump(jobs, f)
                    
                    learn_jobs = [j for j in jobs if j.get('prompt_used') == 'learn_interview']
                    if any(j.get('status') != 'imported' for j in learn_jobs):
                        all_completed = False

                if all_completed:
                    interviews = list((project_dir / 'interviews').glob('interview_*.yaml'))
                    cpf = evaluate_cpf(interviews)
                    
                    all_content = "".join([iv.read_text(encoding='utf-8') for iv in interviews])
                    analysis_hash = hashlib.sha256(all_content.encode('utf-8')).hexdigest()[:16]
                    
                    learn_data = {'cpf_evaluation': cpf, 'analysis_hash': analysis_hash}
                    dest = project_dir / 'reports' / 'learn_results.yaml'
                    with open(dest, 'w', encoding='utf-8') as f:
                        yaml.dump(learn_data, f, allow_unicode=True)
                    update_status(project_dir, 'step3_listen', 'completed')
                    update_status(project_dir, 'step4_learn', 'completed')
                else:
                    update_status(project_dir, 'step4_learn', 'waiting_llm')
                print("Imported learn interview")
            else:
                sys.exit(1)
            if job_record and prompt_used != 'learn_interview' and index_file.exists():
                job_record['status'] = 'imported'
                from datetime import datetime, timezone
                job_record['imported_at'] = datetime.now(timezone.utc).isoformat()
                with open(index_file, 'w', encoding='utf-8') as f:
                    yaml.dump(jobs, f)
        except ValidationError:
            sys.exit(1)

class ReportService:
    @staticmethod
    def generate_report(project_dir: Path):
        report_data = {f"Section {i}": "(データなし)" for i in range(1, 16)}
        
        idea = ""
        if (project_dir / 'idea.md').exists():
            idea = (project_dir / 'idea.md').read_text(encoding='utf-8')
            report_data["Section 1"] = idea if idea else "(データなし)"
            
        index_file = project_dir / 'sources' / 'index.yaml'
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                src_data = yaml.safe_load(f) or {'sources': []}
                sources = src_data.get('sources', [])
                if sources:
                    report_data["Section 2"] = ", ".join([s.get('file_name', '') for s in sources])

        # Load real data for sections
        personas = sorted(list((project_dir / 'personas').glob('*.yaml')))
        if personas:
            names = []
            situations = []
            func_jobs = []
            emo_jobs = []
            soc_jobs = []
            impediments = []
            copings = []
            all_qtv = []
            
            for p_file in personas:
                p_data = yaml.safe_load(open(p_file, 'r', encoding='utf-8'))
                pid = p_data.get('id', p_file.stem)
                names.append(p_data.get('name', '(データなし)'))
                situations.append(p_data.get('situation', '(データなし)'))
                jobs = p_data.get('jobs', {})
                func_jobs.append(jobs.get('functional', '(データなし)'))
                emo_jobs.append(jobs.get('emotional', '(データなし)'))
                soc_jobs.append(jobs.get('social', '(データなし)'))
                impediments.append(p_data.get('impediments', '(データなし)'))
                copings.append(f"{p_data.get('current_coping', '(データなし)')} - {p_data.get('dissatisfaction', '(データなし)')}")
                
                qtv = p_data.get('questions_to_verify', [])
                if qtv:
                    all_qtv.extend([f"- [{pid}] {q}" for q in qtv])
            
            report_data["Section 3"] = "\n\n".join(names)
            report_data["Section 4"] = "\n\n".join(situations)
            report_data["Section 5"] = "\n\n".join(func_jobs)
            report_data["Section 6"] = "\n\n".join(emo_jobs)
            report_data["Section 7"] = "\n\n".join(soc_jobs)
            report_data["Section 8"] = "\n\n".join(impediments)
            report_data["Section 9"] = "\n\n".join(copings)
            report_data["Section 15"] = "\n".join(all_qtv) if all_qtv else "(データなし)"

        alts = project_dir / 'alternatives' / 'alternatives.yaml'
        if alts.exists():
            a_data = yaml.safe_load(open(alts, 'r', encoding='utf-8'))
            report_data["Section 10"] = ", ".join([x['name'] for x in a_data.get('direct_competition', [])]) or '(データなし)'
            report_data["Section 11"] = ", ".join([x['name'] for x in a_data.get('indirect_alternatives', [])]) or '(データなし)'
            report_data["Section 12"] = ", ".join([x['name'] for x in a_data.get('non_consumption', [])]) or '(データなし)'

        # Load learn_results.yaml
        learn_res = project_dir / 'reports' / 'learn_results.yaml'
        if learn_res.exists():
            l_data = yaml.safe_load(open(learn_res, 'r', encoding='utf-8'))
            cpf = l_data.get('cpf_evaluation', {})
            
            ac_file = project_dir / 'reports' / 'ai_completions.yaml'
            ac_text = "(AI補完なし)"
            if ac_file.exists():
                ac_data = yaml.safe_load(open(ac_file, 'r', encoding='utf-8'))
                if ac_data and ac_data.get('ai_completions'):
                    ac_text = yaml.dump(ac_data.get('ai_completions'), allow_unicode=True)
            
            report_data["Section 14"] = "CPF評価:\n" + yaml.dump(cpf, allow_unicode=True) + "\nAI補完:\n" + ac_text
            
        interviews = list((project_dir / 'interviews').glob('interview_*.yaml'))
        quotes = []
        for iv in interviews:
            iv_data = yaml.safe_load(open(iv, 'r', encoding='utf-8'))
            for r in iv_data.get('refutations', []):
                quotes.append(f"[{iv.stem}.md:L{r.get('line')}] \"{r.get('quote')}\"")
        if quotes:
            report_data["Section 13"] = "\n".join(quotes)
        else:
            report_data["Section 13"] = "(データなし)"

        # Check for unstarted steps for section 15
        proj_file = project_dir / 'project.yaml'
        if proj_file.exists():
            with open(proj_file, 'r', encoding='utf-8') as f:
                proj_data = yaml.safe_load(f)
                unstarted = [k for k, v in proj_data.get('status', {}).items() if v == 'unstarted']
                if unstarted:
                    report_data["Section 15"] += "\n未完了ステップ: " + ", ".join(unstarted)

        report = "# Final Report\n\n"
        sections = [
            "初期アイデア",
            "入力資料と出典",
            "対象ペルソナ",
            "ペルソナが置かれた状況",
            "機能的ジョブ",
            "感情的ジョブ",
            "社会的ジョブ",
            "阻害要因",
            "現在の対処方法と不満",
            "直接競合",
            "間接代替",
            "無消費",
            "インタビューから得た事実と引用",
            "反証、CPF評価、AI補完部分",
            "未確認事項と次に確認すべきこと"
        ]
        
        for i in range(1, 16):
            report += f"## {i}. {sections[i-1]}\n{report_data[f'Section {i}']}\n\n"
            
        atomic_write(project_dir / 'reports' / 'final_report.md', report, project_dir)
