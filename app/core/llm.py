"""LLM client setup and utilities supporting multiple providers and deployment types."""

import json
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from openai import AsyncOpenAI
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Tool, FunctionDeclaration
import google.auth
from google.auth.exceptions import DefaultCredentialsError

from app.core.config import settings
from app.utils.logging import logger


class LLMClientConfig:
    """Configuration class for LLM client initialization."""
    
    def __init__(
        self,
        provider: str,
        model: str,
        deployment_type: str = "cloud",
        **kwargs
    ):
        self.provider = provider
        self.model = model
        self.deployment_type = deployment_type
        self.config = kwargs


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, config: LLMClientConfig):
        self.config = config
        self.provider = config.provider
        self.model = config.model
        self.deployment_type = config.deployment_type
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a response using the LLM API."""
        pass
    
    @abstractmethod
    async def generate_embeddings(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> List[List[float]]:
        """Generate embeddings for the given texts."""
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, str]:
        """Get information about the current provider."""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI client wrapper with utility methods."""
    
    def __init__(self, config: LLMClientConfig):
        super().__init__(config)
        
        # Extract OpenAI-specific configuration
        api_key = config.config.get("api_key", settings.openai_api_key)
        base_url = config.config.get("base_url")  # For custom OpenAI-compatible endpoints
        
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
            
        self.client = AsyncOpenAI(**client_kwargs)
        logger.info(f"Initialized OpenAI client with model: {self.model}")
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
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
            
            # Add metadata as extra headers for OpenAI-compatible endpoints
            extra_headers = {}
            if metadata:
                # Merge global metadata with call-specific metadata
                combined_metadata = {**settings.parsed_llm_metadata, **metadata}
                extra_headers.update(combined_metadata)
                logger.info(f"Adding metadata headers to OpenAI request: {list(combined_metadata.keys())}")
            elif settings.parsed_llm_metadata:
                extra_headers.update(settings.parsed_llm_metadata)
                logger.info(f"Adding global metadata headers to OpenAI request: {list(settings.parsed_llm_metadata.keys())}")
            
            if extra_headers:
                kwargs["extra_headers"] = extra_headers
            
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
            logger.error(f"OpenAI API error: {str(e)}")
            raise Exception(f"OpenAI LLM generation failed: {str(e)}")
    
    async def generate_embeddings(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> List[List[float]]:
        """Generate embeddings for the given texts."""
        try:
            kwargs = {
                "model": "text-embedding-ada-002",
                "input": texts
            }
            
            # Add metadata as extra headers for OpenAI-compatible endpoints
            extra_headers = {}
            if metadata:
                # Merge global metadata with call-specific metadata
                combined_metadata = {**settings.parsed_llm_metadata, **metadata}
                extra_headers.update(combined_metadata)
                logger.info(f"Adding metadata headers to OpenAI embeddings request: {list(combined_metadata.keys())}")
            elif settings.parsed_llm_metadata:
                extra_headers.update(settings.parsed_llm_metadata)
                logger.info(f"Adding global metadata headers to OpenAI embeddings request: {list(settings.parsed_llm_metadata.keys())}")
            
            if extra_headers:
                kwargs["extra_headers"] = extra_headers
            
            response = await self.client.embeddings.create(**kwargs)
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            logger.error(f"OpenAI embeddings error: {str(e)}")
            raise Exception(f"OpenAI embedding generation failed: {str(e)}")
    
    def get_provider_info(self) -> Dict[str, str]:
        """Get information about the current provider."""
        info = {
            "provider": "OpenAI",
            "model": self.model,
            "deployment_type": self.deployment_type
        }
        if self.config.config.get("base_url"):
            info["base_url"] = self.config.config["base_url"]
        return info


class VertexAIClient(BaseLLMClient):
    """Google Vertex AI client wrapper with utility methods."""
    
    def __init__(self, config: LLMClientConfig):
        super().__init__(config)
        
        # Extract Vertex AI-specific configuration
        self.project_id = config.config.get("project_id", settings.vertexai_project_id)
        self.location = config.config.get("location", settings.vertexai_location)
        self.credentials_path = config.config.get("credentials_path", settings.google_application_credentials)
        
        # Initialize based on deployment type
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Vertex AI client based on deployment type."""
        try:
            if self.deployment_type == "cloud":
                self._initialize_cloud_client()
            elif self.deployment_type == "on_premise":
                self._initialize_on_premise_client()
            elif self.deployment_type == "corporate":
                self._initialize_corporate_client()
            else:
                raise ValueError(f"Unsupported Vertex AI deployment type: {self.deployment_type}")
                
            logger.info(f"Initialized Vertex AI client ({self.deployment_type}) with model: {self.model} in project: {self.project_id}")
            
        except Exception as e:
            logger.error(f"Vertex AI initialization failed: {str(e)}")
            raise Exception(f"Vertex AI initialization failed: {str(e)}")
    
    def _initialize_cloud_client(self):
        """Initialize for Google Cloud Vertex AI."""
        # Set up authentication
        if self.credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
        
        try:
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.location)
            self.model_client = GenerativeModel(self.model)
        except DefaultCredentialsError as e:
            logger.error(f"Vertex AI authentication failed: {str(e)}")
            raise Exception(f"Vertex AI authentication failed. Please check your credentials: {str(e)}")
    
    def _initialize_on_premise_client(self):
        """Initialize for on-premise Vertex AI deployment."""
        # Extract on-premise specific configuration
        endpoint_url = self.config.config.get("endpoint_url")
        api_key = self.config.config.get("api_key")
        token_function = self.config.config.get("token_function")
        token_function_module = self.config.config.get("token_function_module")
        credentials_function = self.config.config.get("credentials_function")
        credentials_function_module = self.config.config.get("credentials_function_module")
        api_transport = self.config.config.get("api_transport")
        
        if not endpoint_url:
            raise ValueError("endpoint_url is required for on-premise deployment")
        
        try:
            # Handle custom token generation for on-premise
            credentials = None
            
            if token_function and token_function_module:
                # Import and call the in-house token function
                logger.info(f"Using in-house token function: {token_function_module}.{token_function}")
                try:
                    import importlib
                    token_module = importlib.import_module(token_function_module)
                    get_token_func = getattr(token_module, token_function)
                    
                    # Call the token function - it should return a token or credentials
                    token_result = get_token_func()
                    
                    if isinstance(token_result, str):
                        # If it returns a string token, create credentials from it
                        from google.oauth2 import credentials as oauth2_credentials
                        credentials = oauth2_credentials.Credentials(token=token_result)
                        logger.info("Successfully obtained token from in-house function")
                    else:
                        # If it returns credentials object directly
                        credentials = token_result
                        logger.info("Successfully obtained credentials from in-house function")
                        
                except ImportError as e:
                    logger.error(f"Failed to import token module {token_function_module}: {str(e)}")
                    raise ValueError(f"Token function module not found: {token_function_module}")
                except AttributeError as e:
                    logger.error(f"Token function {token_function} not found in module {token_function_module}: {str(e)}")
                    raise ValueError(f"Token function not found: {token_function}")
                except Exception as e:
                    logger.error(f"Error calling token function: {str(e)}")
                    raise ValueError(f"Failed to get token from in-house function: {str(e)}")
            
            elif credentials_function and credentials_function_module:
                # Import and call the in-house credentials function
                logger.info(f"Using in-house credentials function: {credentials_function_module}.{credentials_function}")
                try:
                    import importlib
                    creds_module = importlib.import_module(credentials_function_module)
                    get_credentials_func = getattr(creds_module, credentials_function)
                    
                    # Call the credentials function
                    credentials = get_credentials_func()
                    logger.info("Successfully obtained credentials from in-house function")
                    
                except ImportError as e:
                    logger.error(f"Failed to import credentials module {credentials_function_module}: {str(e)}")
                    raise ValueError(f"Credentials function module not found: {credentials_function_module}")
                except AttributeError as e:
                    logger.error(f"Credentials function {credentials_function} not found in module {credentials_function_module}: {str(e)}")
                    raise ValueError(f"Credentials function not found: {credentials_function}")
                except Exception as e:
                    logger.error(f"Error calling credentials function: {str(e)}")
                    raise ValueError(f"Failed to get credentials from in-house function: {str(e)}")
            
            elif api_key:
                # Fallback to API key if no custom function is provided
                logger.info("Using API key for on-premise authentication")
                os.environ["GOOGLE_API_KEY"] = api_key
            
            # Initialize Vertex AI with custom endpoint and credentials
            init_kwargs = {
                "project": self.project_id,
                "location": self.location,
                "api_endpoint": endpoint_url
            }
            
            if credentials:
                init_kwargs["credentials"] = credentials
                logger.info("Initializing Vertex AI with custom credentials")
            
            if api_transport:
                init_kwargs["api_transport"] = api_transport
                logger.info(f"Initializing Vertex AI with custom API transport: {api_transport}")
            
            vertexai.init(**init_kwargs)
            self.model_client = GenerativeModel(self.model)
            
        except Exception as e:
            logger.error(f"On-premise Vertex AI initialization failed: {str(e)}")
            raise
    
    def _initialize_corporate_client(self):
        """Initialize for corporate hosted Gemini models."""
        # Extract corporate-specific configuration
        endpoint_url = self.config.config.get("endpoint_url")
        api_key = self.config.config.get("api_key")
        auth_method = self.config.config.get("auth_method", "api_key")
        
        if not endpoint_url:
            raise ValueError("endpoint_url is required for corporate deployment")
        
        try:
            if auth_method == "api_key" and api_key:
                # Use API key authentication for corporate deployment
                # This might require custom headers or different initialization
                os.environ["GOOGLE_API_KEY"] = api_key
            
            # Initialize with custom endpoint
            vertexai.init(
                project=self.project_id or "corporate-project",
                location=self.location or "corporate-location",
                api_endpoint=endpoint_url
            )
            self.model_client = GenerativeModel(self.model)
            
        except Exception as e:
            logger.error(f"Corporate Vertex AI initialization failed: {str(e)}")
            raise
    
    def _convert_messages_to_vertex_format(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to Vertex AI prompt format."""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Add final prompt for assistant response
        prompt_parts.append("Assistant:")
        
        return "\n\n".join(prompt_parts)
    
    def _convert_tools_to_vertex_format(self, tools: List[Dict[str, Any]]) -> List[Tool]:
        """Convert OpenAI-style tools to Vertex AI format."""
        vertex_tools = []
        
        for tool in tools:
            if tool.get("type") == "function":
                func_info = tool.get("function", {})
                function_declaration = FunctionDeclaration(
                    name=func_info.get("name"),
                    description=func_info.get("description"),
                    parameters=func_info.get("parameters", {})
                )
                vertex_tools.append(Tool(function_declarations=[function_declaration]))
        
        return vertex_tools
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a response using Vertex AI API."""
        try:
            # Convert messages to Vertex AI format
            prompt = self._convert_messages_to_vertex_format(messages)
            
            # Set up generation config
            generation_config = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            
            # Handle tools - Vertex AI has limitations with multiple tools
            vertex_tools = None
            if tools:
                # Vertex AI (Gemini) currently supports only one tool at a time
                # We'll implement a smart selection strategy instead of just warning
                if len(tools) > 1:
                    # Strategy 1: Check if all tools are related (same domain) - we could combine them
                    all_db_tools = all(any(keyword in t.get('function', {}).get('name', '').lower() 
                                          for keyword in ['query', 'metrics', 'database', 'get_', 'search']) 
                                      for t in tools)
                    
                    if all_db_tools and len(tools) <= 3:
                        # For a small number of related database tools, create a combined description
                        # and let the LLM choose which one to use in its response
                        combined_description = f"Database tools available: {', '.join(t['function']['name'] for t in tools)}. "
                        combined_description += "Available operations: " + "; ".join(
                            f"{t['function']['name']}: {t['function'].get('description', 'No description')}" 
                            for t in tools
                        )
                        
                        # Use the first tool but enhance its description
                        selected_tool = tools[0].copy()
                        selected_tool['function']['description'] = combined_description
                        tool_reason = f"enhanced tool '{selected_tool['function']['name']}' (representing {len(tools)} database tools)"
                    else:
                        # Strategy 2: Prefer database/query tools over general tools
                        db_tools = [t for t in tools if any(keyword in t.get('function', {}).get('name', '').lower() 
                                                           for keyword in ['query', 'metrics', 'database', 'get_', 'search'])]
                        
                        if db_tools:
                            selected_tool = db_tools[0]  # Use first database-related tool
                            tool_reason = f"database tool '{selected_tool['function']['name']}'"
                        else:
                            # Strategy 3: Use the first tool as fallback
                            selected_tool = tools[0]
                            tool_reason = f"first available tool '{selected_tool['function']['name']}'"
                    
                    logger.info(f"Vertex AI limitation: Using {tool_reason} from {len(tools)} available tools")
                    tools = [selected_tool]
                
                vertex_tools = self._convert_tools_to_vertex_format(tools)
            
            # Handle metadata for Vertex AI requests
            request_metadata = {}
            if metadata:
                # Merge global metadata with call-specific metadata
                combined_metadata = {**settings.parsed_llm_metadata, **metadata}
                request_metadata.update(combined_metadata)
                logger.info(f"Adding metadata to Vertex AI request: {list(combined_metadata.keys())}")
            elif settings.parsed_llm_metadata:
                request_metadata.update(settings.parsed_llm_metadata)
                logger.info(f"Adding global metadata to Vertex AI request: {list(settings.parsed_llm_metadata.keys())}")
            
            # Generate response
            request_kwargs = {
                "generation_config": generation_config
            }
            
            # For Vertex AI, metadata can be passed as custom request headers via the client context
            # This is most useful for corporate/on-premise deployments where custom headers are needed
            if request_metadata and hasattr(self.model_client, '_client') and hasattr(self.model_client._client, '_metadata'):
                # Add metadata as gRPC metadata for Vertex AI
                import grpc
                metadata_items = [(k, str(v)) for k, v in request_metadata.items()]
                request_kwargs["metadata"] = metadata_items
            
            if vertex_tools:
                response = await self.model_client.generate_content_async(
                    prompt,
                    tools=vertex_tools,
                    **request_kwargs
                )
            else:
                response = await self.model_client.generate_content_async(
                    prompt,
                    **request_kwargs
                )
            
            result = {
                "content": "",
                "tool_calls": []
            }
            
            # Handle function calls if present
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            func_call = part.function_call
                            result["tool_calls"].append({
                                "id": f"call_{func_call.name}",
                                "function": {
                                    "name": func_call.name,
                                    "arguments": dict(func_call.args) if func_call.args else {}
                                }
                            })
                        elif hasattr(part, 'text') and part.text:
                            result["content"] += part.text
            
            # If no function calls, try to get the text response
            if not result["tool_calls"] and response.text:
                result["content"] = response.text
            
            return result
            
        except Exception as e:
            logger.error(f"Vertex AI API error: {str(e)}")
            raise Exception(f"Vertex AI LLM generation failed: {str(e)}")
    
    async def generate_embeddings(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> List[List[float]]:
        """Generate embeddings for the given texts using Vertex AI."""
        try:
            from vertexai.language_models import TextEmbeddingModel
            
            # Handle metadata for Vertex AI embedding requests
            request_metadata = {}
            if metadata:
                # Merge global metadata with call-specific metadata
                combined_metadata = {**settings.parsed_llm_metadata, **metadata}
                request_metadata.update(combined_metadata)
                logger.info(f"Adding metadata to Vertex AI embeddings request: {list(combined_metadata.keys())}")
            elif settings.parsed_llm_metadata:
                request_metadata.update(settings.parsed_llm_metadata)
                logger.info(f"Adding global metadata to Vertex AI embeddings request: {list(settings.parsed_llm_metadata.keys())}")
            
            # Get the embedding model name from settings
            embedding_model_name = getattr(settings, 'embeddings_model', 'text-embedding-005')
            
            # Initialize the embedding model
            embedding_model = TextEmbeddingModel.from_pretrained(embedding_model_name)
            
            # Generate embeddings for all texts
            embeddings_list = []
            
            # Process texts in batches to avoid API limits
            batch_size = 5  # Vertex AI has rate limits
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # Generate embeddings for this batch
                batch_embeddings = []
                for text in batch_texts:
                    # Prepare embedding kwargs
                    embedding_kwargs = {"input": [text]}
                    
                    # Add metadata for corporate/on-premise deployments if available
                    # Note: For standard Vertex AI, metadata is typically handled at the client level
                    # For custom endpoints, metadata might be passed differently
                    
                    # Generate embeddings (task_type may not be supported in all versions)
                    try:
                        # Try with task_type first for newer models
                        if embedding_model_name in ['text-embedding-004', 'text-embedding-005', 'gemini-embedding-001']:
                            embedding = embedding_model.get_embeddings([text], task_type="RETRIEVAL_DOCUMENT")
                        else:
                            embedding = embedding_model.get_embeddings([text])
                    except TypeError:
                        # Fallback if task_type is not supported
                        embedding = embedding_model.get_embeddings([text])
                    
                    # Extract the vector values
                    if hasattr(embedding[0], 'values'):
                        batch_embeddings.append(embedding[0].values)
                    else:
                        # Fallback for different API versions
                        batch_embeddings.append(embedding[0])
                
                embeddings_list.extend(batch_embeddings)
            
            logger.info(f"Generated {len(embeddings_list)} embeddings using Vertex AI model: {embedding_model_name}")
            return embeddings_list
            
        except ImportError:
            logger.error("Vertex AI language models not available. Please install google-cloud-aiplatform.")
            raise Exception("Vertex AI embedding generation failed: Missing dependencies")
        except Exception as e:
            logger.error(f"Vertex AI embeddings error: {str(e)}")
            raise Exception(f"Vertex AI embedding generation failed: {str(e)}")
    
    def get_provider_info(self) -> Dict[str, str]:
        """Get information about the current provider."""
        info = {
            "provider": "Google Vertex AI",
            "model": self.model,
            "project": self.project_id,
            "location": self.location,
            "deployment_type": self.deployment_type
        }
        
        if self.deployment_type in ["on_premise", "corporate"]:
            endpoint_url = self.config.config.get("endpoint_url")
            if endpoint_url:
                info["endpoint_url"] = endpoint_url
        
        return info


class LLMClientFactory:
    """Factory class for creating LLM clients based on configuration."""
    
    @staticmethod
    def create_client(config: LLMClientConfig) -> BaseLLMClient:
        """Create an LLM client based on the provided configuration."""
        if config.provider == "openai":
            return OpenAIClient(config)
        elif config.provider == "vertexai":
            return VertexAIClient(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")
    
    @staticmethod
    def create_from_settings() -> BaseLLMClient:
        """Create an LLM client from application settings."""
        if settings.llm_provider == "openai":
            config = LLMClientConfig(
                provider="openai",
                model=settings.openai_model,
                deployment_type="cloud",
                api_key=settings.openai_api_key
            )
        elif settings.llm_provider == "vertexai":
            config = LLMClientConfig(
                provider="vertexai",
                model=settings.vertexai_model,
                deployment_type=getattr(settings, 'vertexai_deployment_type', 'cloud'),
                project_id=settings.vertexai_project_id,
                location=settings.vertexai_location,
                credentials_path=settings.google_application_credentials,
                # Additional configuration for different deployment types
                endpoint_url=getattr(settings, 'vertexai_endpoint_url', None),
                api_key=getattr(settings, 'vertexai_api_key', None),
                auth_method=getattr(settings, 'vertexai_auth_method', 'default'),
                # On-premise authentication configuration
                token_function=getattr(settings, 'vertexai_token_function', None),
                token_function_module=getattr(settings, 'vertexai_token_function_module', None),
                credentials_function=getattr(settings, 'vertexai_credentials_function', None),
                credentials_function_module=getattr(settings, 'vertexai_credentials_function_module', None),
                # On-premise transport configuration
                api_transport=getattr(settings, 'vertexai_api_transport', None)
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
        
        return LLMClientFactory.create_client(config)


class LLMClient:
    """Unified LLM client that supports multiple providers and deployment types."""
    
    def __init__(self):
        self.client = LLMClientFactory.create_from_settings()
        self.provider = self.client.provider
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a response using the configured LLM provider."""
        return await self.client.generate_response(
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata
        )
    
    async def generate_embeddings(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> List[List[float]]:
        """Generate embeddings for the given texts."""
        return await self.client.generate_embeddings(texts, metadata)
    
    def get_provider_info(self) -> Dict[str, str]:
        """Get information about the current LLM provider."""
        return self.client.get_provider_info()


# Global LLM client instance
llm_client = LLMClient() 