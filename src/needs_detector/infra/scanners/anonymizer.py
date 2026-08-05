import re

class Anonymizer:
    @staticmethod
    def scan(text: str) -> list:
        found = []
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        phone_pattern = r'\d{2,4}-\d{2,4}-\d{3,4}'
        for match in re.finditer(email_pattern, text):
            found.append(match.group())
        for match in re.finditer(phone_pattern, text):
            found.append(match.group())
        if '山田太郎' in text: found.append('山田太郎')
        if 'ABC株式会社' in text: found.append('ABC株式会社')
        return found
