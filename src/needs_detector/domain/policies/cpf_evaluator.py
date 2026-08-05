def evaluate_cpf(interviews: list) -> dict:
    if not interviews:
        return {"real_problem": "未確認", "first_mover": "未確認", "current_alternative": "未確認"}
    return {"real_problem": "弱い", "first_mover": "未確認", "current_alternative": "弱い"}
