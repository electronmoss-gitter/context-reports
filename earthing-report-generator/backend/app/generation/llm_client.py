"""
LLM Client - Interface with Anthropic Claude API
"""
from anthropic import Anthropic
from typing import Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    """Client for interacting with Claude API"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 8000,
        temperature: float = 0.3
    ):
        """
        Initialize the LLM client
        
        Args:
            api_key: Anthropic API key (uses env var if not provided)
            model: Model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or provided")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
    
    def generate(
        self, 
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Claude
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters for the API
            
        Returns:
            Generated text
        """
        try:
            # Build messages
            messages = [{"role": "user", "content": prompt}]
            
            # Call API (updated for anthropic 0.7.8)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                temperature=kwargs.get('temperature', self.temperature),
                system=system_prompt or "You are a technical report writing assistant specialized in electrical engineering.",
                messages=messages
            )
            
            # Extract text from response
            return response.content[0].text
            
        except Exception as e:
            raise Exception(f"Error generating text: {str(e)}")
    
    def generate_structured(
        self,
        prompt: str,
        schema: Dict,
        system_prompt: Optional[str] = None
    ) -> Dict:
        """
        Generate structured output following a schema
        
        Args:
            prompt: User prompt
            schema: JSON schema for output
            system_prompt: Optional system prompt
            
        Returns:
            Parsed JSON response
        """
        import json
        
        # Add schema to prompt
        enhanced_prompt = f"{prompt}\n\nPlease respond with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
        
        response = self.generate(enhanced_prompt, system_prompt)
        
        # Parse JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            raise ValueError(f"Could not parse JSON from response: {response}")