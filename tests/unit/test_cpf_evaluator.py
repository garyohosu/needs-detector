import pytest
from needs_detector.domain.policies.cpf_evaluator import evaluate_cpf

def test_cpf_evaluation_levels():
    res_empty = evaluate_cpf([])
    assert res_empty['real_problem'] == '未確認'

    res_some = evaluate_cpf([{}])
    assert res_some['real_problem'] == '弱い'
