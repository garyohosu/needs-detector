import re

class QuestionChecker:
    @staticmethod
    def check(question: str) -> dict:
        patterns = [
            (r'使いますか|購入しますか|利用したいですか', '過去の行動について質問してください'),
            (r'機能があれば欲しいですか|便利だと思いますか', '過去の行動について質問してください'),
            (r'困っていませんか|不便ですよね', '具体的な経験を教えてください')
        ]
        for pattern, suggestion in patterns:
            if re.search(pattern, question):
                return {'is_warning': True, 'reason': '誘導質問の可能性があります', 'suggestion': suggestion}
        return {'is_warning': False}
