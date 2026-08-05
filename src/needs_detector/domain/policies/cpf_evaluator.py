import yaml

def evaluate_cpf(interviews: list) -> dict:
    if not interviews:
        return {"real_problem": "未確認", "first_mover": "未確認", "current_alternative": "未確認"}
    
    concrete_events = 0
    cost_time_evidence = 0
    
    for iv in interviews:
        with open(iv, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        content = data.get('content', '')
        # Simple heuristic since LLM does it usually
        if 'time' in content or 'cost' in content or '時間' in content or 'お金' in content:
            cost_time_evidence += 1
        if 'event' in content or '出来事' in content or '行動' in content:
            concrete_events += 1
            
    if concrete_events > 0 and cost_time_evidence > 0:
        eval_val = "強い"
    elif concrete_events > 0:
        eval_val = "一部確認"
    else:
        eval_val = "弱い"
        
    return {"real_problem": eval_val, "first_mover": eval_val, "current_alternative": eval_val}

