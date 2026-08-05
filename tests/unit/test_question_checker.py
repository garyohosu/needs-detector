import pytest
from needs_detector.domain.policies.question_checker import QuestionChecker

def test_leading_question_warning():
    res1 = QuestionChecker.check("このサービスを使いますか？")
    assert res1['is_warning'] is True

    res2 = QuestionChecker.check("この機能があれば便利だと思いますか？")
    assert res2['is_warning'] is True

    res3 = QuestionChecker.check("最後にその課題に直面したのはいつですか？")
    assert res3['is_warning'] is False
