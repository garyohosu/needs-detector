from abc import ABC, abstractmethod
class LLMResponse:
    def __init__(self, content, ai_completions, prompt_used, model_name):
        self.content = content
        self.ai_completions = ai_completions
        self.prompt_used = prompt_used
        self.model_name = model_name

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt_name, context):
        pass

class MockLLMProvider(LLMProvider):
    def generate(self, prompt_name, context):
        return LLMResponse(content='mock response', ai_completions=[], prompt_used=prompt_name, model_name='mock')

class ManualLLMProvider(LLMProvider):
    def generate(self, prompt_name, context):
        return LLMResponse(content='manual response', ai_completions=[], prompt_used=prompt_name, model_name='manual')
