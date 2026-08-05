import re

class Anonymizer:
    @staticmethod
    def scan(text: str) -> list:
        found = []
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        phone_pattern = r'0\d{1,4}-\d{1,4}-\d{3,4}'
        postal_pattern = r'\d{3}-\d{4}'
        url_pattern = r'https?://\S+'
        ipv4_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
        
        patterns = [email_pattern, phone_pattern, postal_pattern, url_pattern, ipv4_pattern]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                found.append(match.group())
                
        return found
