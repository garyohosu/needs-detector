import yaml
from pathlib import Path

def evaluate_cpf(interviews: list) -> dict:
    if not interviews:
        return {"real_problem": "未確認", "first_mover": "未確認", "current_alternative": "未確認"}
    
    real_problem_score = 0
    first_mover_score = 0
    current_alternative_score = 0
    
    for iv in interviews:
        with open(iv, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        content = data.get('content', '')
        refutations = data.get('refutations', [])
        
        for r in refutations:
            q = r.get('quote', '')
            ev = r.get('evidence', {})
            if ev:
                ev_content = ev.get('content', '')
            else:
                ev_content = ''
                
            combined = q + " " + ev_content + " " + content
            combined = combined.lower()
            
            # real_problem: concrete events, frequency, impact
            if 'event' in combined or '出来事' in combined or '行動' in combined or '頻繁' in combined or 'often' in combined:
                real_problem_score += 1
                
            # first_mover: time spent, money spent, consultations, trials
            if 'time' in combined or 'cost' in combined or '時間' in combined or 'お金' in combined or 'tried' in combined or '試し' in combined:
                first_mover_score += 1
                
            # current_alternative: specific alternative identified, dissatisfaction, reason still used
            if 'alternative' in combined or '代わり' in combined or 'dissatisfied' in combined or '不満' in combined or 'but' in combined:
                current_alternative_score += 1

    def get_level(score):
        if score >= 2: return "強い"
        elif score == 1: return "一部確認"
        return "弱い"

    return {
        "real_problem": get_level(real_problem_score),
        "first_mover": get_level(first_mover_score),
        "current_alternative": get_level(current_alternative_score)
    }
