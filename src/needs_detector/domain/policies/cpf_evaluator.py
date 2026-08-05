import yaml
from pathlib import Path

def evaluate_cpf(interviews: list) -> dict:
    if not interviews:
        return {"real_problem": "未確認", "first_mover": "未確認", "current_alternative": "未確認"}
    
    total_evidence = {
        "real_problem": {"concrete_events": [], "frequency": [], "impact": []},
        "first_mover": {"time_spent": [], "money_spent": [], "attempts": []},
        "current_alternative": {"alternatives_used": [], "dissatisfaction": [], "continued_use_reason": []}
    }
    
    for iv in interviews:
        with open(iv, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        cpf = data.get('cpf_evidence', {})
        if not cpf:
            continue
            
        for axis in ['real_problem', 'first_mover', 'current_alternative']:
            axis_data = cpf.get(axis, {})
            for field, items in axis_data.items():
                if isinstance(items, list):
                    total_evidence[axis][field].extend(items)

    def get_level(evidence_category):
        score = sum(1 for v in evidence_category.values() if v) # number of fields with >= 1 item
        if score >= 2: return "強い"
        elif score == 1: return "一部確認"
        return "弱い"

    return {
        "cpf_evidence": total_evidence,
        "evaluations": {
            "real_problem": get_level(total_evidence["real_problem"]),
            "first_mover": get_level(total_evidence["first_mover"]),
            "current_alternative": get_level(total_evidence["current_alternative"])
        }
    }
