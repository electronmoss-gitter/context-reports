from anthropic import Anthropic

class ClaudeClient:
    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)
    
    def generate_section(prompt, context):
        # Call Claude API with project data + RAG context
        pass