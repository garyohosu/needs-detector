import pytest
import subprocess
import sys
import json
import yaml
from pathlib import Path

def run_cmd(cmd, cwd):
    import os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent / "src")
    res = subprocess.run([sys.executable, "-m", "needs_detector.cli.main"] + cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    assert res.returncode == 0, f"Command {' '.join(cmd)} failed: {res.stderr}"
    return res.stdout

def test_manual_e2e(tmp_path):
    project_dir = tmp_path / "test_proj"
    
    # 1. init
    run_cmd(["init", "test_proj", "--dir", str(tmp_path)], tmp_path)
    
    # 2. add-idea
    idea_path = tmp_path / "idea.md"
    idea_path.write_text("Test idea")
    run_cmd(["add-idea", str(idea_path)], project_dir)
    
    # 3. add-source
    src_path = tmp_path / "src.md"
    src_path.write_text("Source content")
    run_cmd(["add-source", str(src_path)], project_dir)
    
    # 4. draw
    run_cmd(["draw", "--provider", "manual"], project_dir)
    
    with open(project_dir / "project.yaml") as f:
        proj = yaml.safe_load(f)
        assert proj["status"]["step1_draw"] == "waiting_llm"
        
    with open(project_dir / "manual_prompts" / "index.yaml") as f:
        jobs = yaml.safe_load(f)
        draw_job = next(j for j in jobs if j["prompt_used"] == "draw_persona")
        
    draw_resp = {
        "job_id": draw_job["job_id"],
        "prompt_used": "draw_persona",
        "content": {
            "personas": [
                {
                    "id": "p1",
                    "name": "Test Persona",
                    "situation": "Test Sit",
                    "jobs": {"functional": "A", "emotional": "B", "social": "C"},
                    "impediments": "imp",
                    "current_coping": "cope",
                    "dissatisfaction": "diss",
                    "evidence_type": "hypothesis",
                    "source_reference": "src.md",
                    "questions_to_verify": ["q1"]
                }
            ]
        }
    }
    
    draw_resp_path = tmp_path / "draw_resp.json"
    draw_resp_path.write_text(json.dumps(draw_resp))
    
    # 5. import draw
    run_cmd(["import-llm-response", str(draw_resp_path)], project_dir)
    with open(project_dir / "project.yaml") as f:
        assert yaml.safe_load(f)["status"]["step1_draw"] == "completed"

    # 6. explore
    run_cmd(["explore", "--provider", "manual"], project_dir)
    
    with open(project_dir / "manual_prompts" / "index.yaml") as f:
        explore_job = next(j for j in yaml.safe_load(f) if j["prompt_used"] == "explore_alternatives")
        
    explore_resp = {
        "job_id": explore_job["job_id"],
        "prompt_used": "explore_alternatives",
        "content": {
            "direct_competition": [{"name": "A", "benefits": "a", "problems": "b", "cost_time": "c"}],
            "indirect_alternatives": [],
            "non_consumption": []
        }
    }
    
    explore_resp_path = tmp_path / "explore_resp.json"
    explore_resp_path.write_text(json.dumps(explore_resp))
    
    # 7. import explore
    run_cmd(["import-llm-response", str(explore_resp_path)], project_dir)
    with open(project_dir / "project.yaml") as f:
        assert yaml.safe_load(f)["status"]["step2_explore"] == "completed"

    # 8. guide
    run_cmd(["interview-guide", "--provider", "manual"], project_dir)
    
    with open(project_dir / "manual_prompts" / "index.yaml") as f:
        guide_job = next(j for j in yaml.safe_load(f) if j["prompt_used"] == "interview_guide")
        
    guide_resp = {
        "job_id": guide_job["job_id"],
        "prompt_used": "interview_guide",
        "content": {
            "core_questions": ["Q1"],
            "deep_dive_questions": ["Q2"]
        }
    }
    
    guide_resp_path = tmp_path / "guide_resp.json"
    guide_resp_path.write_text(json.dumps(guide_resp))
    
    # 9. import guide
    run_cmd(["import-llm-response", str(guide_resp_path)], project_dir)
    with open(project_dir / "project.yaml") as f:
        assert yaml.safe_load(f)["status"]["step3_listen"] == "in_progress"

    # 10, 11 add-interview
    iv1_path = tmp_path / "iv1.md"
    iv1_path.write_text("Hello line1")
    run_cmd(["add-interview", str(iv1_path)], project_dir)
    
    iv2_path = tmp_path / "iv2.md"
    iv2_path.write_text("Hello line2")
    run_cmd(["add-interview", str(iv2_path)], project_dir)

    # 12 learn
    run_cmd(["learn", "--provider", "manual"], project_dir)
    
    with open(project_dir / "project.yaml") as f:
        assert yaml.safe_load(f)["status"]["step4_learn"] == "waiting_llm"
        
    with open(project_dir / "manual_prompts" / "index.yaml") as f:
        learn_jobs = [j for j in yaml.safe_load(f) if j["prompt_used"] == "learn_interview"]
    
    assert len(learn_jobs) == 2
    
    learn_resp1 = {
        "job_id": learn_jobs[0]["job_id"],
        "prompt_used": "learn_interview",
        "target": learn_jobs[0]["target"],
        "content": {
            "refutations": [
                {
                    "quote": "Hello line1",
                    "line": 1,
                    "source": learn_jobs[0]["target"],
                    "evidence": {
                        "evidence_type": "quote",
                        "content": "Hello line1",
                        "source_ref": f"{learn_jobs[0]['target']}.yaml:1"
                    }
                }
            ],
            "cpf_evidence": {
                "real_problem": {
                    "concrete_events": ["Test Event 1"],
                    "frequency": ["Daily"],
                    "impact": ["High"]
                },
                "first_mover": {
                    "time_spent": ["1h"],
                    "money_spent": [],
                    "attempts": ["Many"]
                },
                "current_alternative": {
                    "alternatives_used": ["None"],
                    "dissatisfaction": ["Bad"],
                    "continued_use_reason": ["None"]
                }
            }
        },
        "ai_completions": [{"content": "Interview 1 AI completion", "related_artifact": f"interviews/{learn_jobs[0]['target']}.yaml"}]
    }
    lr1_path = tmp_path / "lr1.json"
    lr1_path.write_text(json.dumps(learn_resp1))
    
    learn_resp2 = {
        "job_id": learn_jobs[1]["job_id"],
        "prompt_used": "learn_interview",
        "target": learn_jobs[1]["target"],
        "content": {
            "refutations": [
                {
                    "quote": "Hello line2",
                    "line": 1,
                    "source": learn_jobs[1]["target"],
                    "evidence": {
                        "evidence_type": "quote",
                        "content": "Hello line2",
                        "source_ref": f"{learn_jobs[1]['target']}.yaml:1"
                    }
                }
            ],
            "cpf_evidence": {
                "real_problem": {
                    "concrete_events": ["Test Event 2"],
                    "frequency": ["Weekly"],
                    "impact": ["Medium"]
                },
                "first_mover": {
                    "time_spent": ["2h"],
                    "money_spent": [],
                    "attempts": ["Few"]
                },
                "current_alternative": {
                    "alternatives_used": ["Excel"],
                    "dissatisfaction": ["Slow"],
                    "continued_use_reason": ["Free"]
                }
            }
        },
        "ai_completions": [{"content": "Interview 2 AI completion", "related_artifact": f"interviews/{learn_jobs[1]['target']}.yaml"}]
    }
    lr2_path = tmp_path / "lr2.json"
    lr2_path.write_text(json.dumps(learn_resp2))
    
    # 13 import learn 1
    run_cmd(["import-llm-response", str(lr1_path)], project_dir)
    with open(project_dir / "project.yaml") as f:
        assert yaml.safe_load(f)["status"]["step4_learn"] == "waiting_llm"
        
    # 14 import learn 2
    run_cmd(["import-llm-response", str(lr2_path)], project_dir)
    with open(project_dir / "project.yaml") as f:
        assert yaml.safe_load(f)["status"]["step4_learn"] == "completed"

    # 15 report
    run_cmd(["report"], project_dir)
    report_file = project_dir / "reports" / "final_report.md"
    assert report_file.exists()
    report_content = report_file.read_text(encoding="utf-8")
    assert "Test Persona" in report_content
    assert "Hello line1" in report_content
    assert "Hello line2" in report_content
    assert "Test Event 1" in report_content
    assert "Test Event 2" in report_content
    assert "real_problem" in report_content
    assert "first_mover" in report_content
    assert "current_alternative" in report_content
    assert "Interview 1 AI completion" in report_content
    assert "Interview 2 AI completion" in report_content
