"""OpenAI client setup and LLM utilities."""

from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
import json

from app.core.config import settings


class LLMClient:
    """OpenAI client wrapper with utility methods."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a response using OpenAI API."""
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = await self.client.chat.completions.create(**kwargs)
            
            # Extract the response
            message = response.choices[0].message
            
            result = {
                "content": message.content,
                "tool_calls": []
            }
            
            # Handle tool calls if present
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": json.loads(tool_call.function.arguments)
                        }
                    })
            
            return result
            
        except Exception as e:
            raise Exception(f"LLM generation failed: {str(e)}")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for the given texts."""
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            raise Exception(f"Embedding generation failed: {str(e)}")


# Global LLM client instance
llm_client = LLMClient() 