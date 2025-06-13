"""LLM client setup and utilities supporting multiple providers and deployment types."""

import json
import os
import sys
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from openai import AsyncOpenAI
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Tool, FunctionDeclaration
import google.auth
from google.auth.exceptions import DefaultCredentialsError
import traceback

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
            # Log input parameters for debugging
            logger.info(f"OpenAI generate_response called with: messages={len(messages)}, tools={len(tools) if tools else 0}, temperature={temperature}, max_tokens={max_tokens}, metadata={list(metadata.keys()) if metadata else 'None'}")
            
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
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
            
            # Make the API call
            response = await self.client.chat.completions.create(**kwargs)
            
            # Process response
            result = {
                "content": response.choices[0].message.content or "",
                "tool_calls": []
            }
            
            # Handle tool calls if present
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                        }
                    })
            
            return result
            
        except Exception as e:
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"OpenAI API error at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
            logger.error(f"Input parameters - messages: {len(messages)} items, tools: {len(tools) if tools else 0}, temperature: {temperature}, max_tokens: {max_tokens}, metadata: {list(metadata.keys()) if metadata else 'None'}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise Exception(f"OpenAI LLM generation failed: {str(e)}")
    
    async def generate_embeddings(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> List[List[float]]:
        """Generate embeddings for the given texts."""
        try:
            # Log input parameters for debugging
            logger.info(f"OpenAI generate_embeddings called with: texts={len(texts)}, metadata={list(metadata.keys()) if metadata else 'None'}")
            
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
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"OpenAI embeddings error at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
            logger.error(f"Input parameters - texts: {len(texts)}, metadata: {list(metadata.keys()) if metadata else 'None'}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
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
        self.api_transport = config.config.get("api_transport")
        
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
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"Vertex AI initialization failed at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
            logger.error(f"Input parameters - deployment_type: {self.deployment_type}, model: {self.model}, project_id: {self.project_id}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise Exception(f"Vertex AI initialization failed: {str(e)}")
    
    def _initialize_cloud_client(self):
        """Initialize for Google Cloud Vertex AI."""
        # Set up authentication
        if self.credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
        
        try:
            # Log detailed parameters before vertexai.init call
            init_params = {
                "project": self.project_id,
                "location": self.location
            }
            logger.info(f"VERTEXAI_INIT_CALL [Cloud]: Calling vertexai.init with parameters: {init_params}")
            logger.info(f"VERTEXAI_INIT_CALL [Cloud]: project={self.project_id}, location={self.location}")
            logger.info(f"VERTEXAI_INIT_CALL [Cloud]: credentials_path={self.credentials_path}")
            logger.info(f"VERTEXAI_INIT_CALL [Cloud]: deployment_type={self.deployment_type}")
            logger.info(f"VERTEXAI_INIT_CALL [Cloud]: model={self.model}")
            
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.location)
            self.model_client = GenerativeModel(self.model)
        except DefaultCredentialsError as e:
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"Vertex AI authentication failed at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
            logger.error(f"Input parameters - project_id: {self.project_id}, location: {self.location}, credentials_path: {self.credentials_path}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise Exception(f"Vertex AI authentication failed. Please check your credentials: {str(e)}")
    
    def _initialize_on_premise_client(self):
        """Initialize for on-premise Vertex AI deployment."""
        # Extract on-premise specific configuration
        endpoint_url = self.config.config.get("endpoint_url")
        api_key = self.config.config.get("api_key")
        auth_method = self.config.config.get("auth_method", "default")
        token_function = self.config.config.get("token_function")
        token_function_module = self.config.config.get("token_function_module")
        credentials_function = self.config.config.get("credentials_function")
        credentials_function_module = self.config.config.get("credentials_function_module")
        api_transport = self.config.config.get("api_transport")
        
        # SSL Configuration
        ssl_verify = self.config.config.get("ssl_verify", True)
        ssl_ca_cert_path = self.config.config.get("ssl_ca_cert_path")
        
        # Debug logging for SSL configuration
        logger.info(f"VERTEXAI_SSL_DEBUG [On-Premise]: SSL configuration:")
        logger.info(f"VERTEXAI_SSL_DEBUG [On-Premise]: ssl_verify={ssl_verify}")
        logger.info(f"VERTEXAI_SSL_DEBUG [On-Premise]: ssl_ca_cert_path={ssl_ca_cert_path}")
        
        # Handle SSL verification settings
        if not ssl_verify:
            logger.warning(f"VERTEXAI_SSL_WARNING [On-Premise]: SSL certificate verification is DISABLED")
            logger.warning(f"VERTEXAI_SSL_WARNING [On-Premise]: This is insecure and should only be used in development")
            # Disable SSL warnings when verification is disabled
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Set environment variables to disable SSL verification
            import os
            os.environ["PYTHONHTTPSVERIFY"] = "0"
            os.environ["CURL_CA_BUNDLE"] = ""
            os.environ["REQUESTS_CA_BUNDLE"] = ""
        
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
                        logger.info(f"VERTEXAI_CREDENTIALS_DEBUG: Created credentials object from token string")
                        logger.info(f"VERTEXAI_CREDENTIALS_DEBUG: credentials type={type(credentials)}")
                    else:
                        # Use the result directly as credentials object
                        credentials = token_result
                        logger.info("Successfully obtained credentials from in-house function")
                        logger.info(f"VERTEXAI_CREDENTIALS_DEBUG: Using credentials object directly")
                        logger.info(f"VERTEXAI_CREDENTIALS_DEBUG: credentials type={type(credentials)}")
                    
                except ImportError as e:
                    # Enhanced exception logging with traceback and input parameters
                    logger.error(f"Failed to import token module at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
                    logger.error(f"Input parameters - token_function_module: {token_function_module}, token_function: {token_function}")
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    raise ValueError(f"Token function module not found: {token_function_module}")
                except AttributeError as e:
                    # Enhanced exception logging with traceback and input parameters
                    logger.error(f"Token function not found at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
                    logger.error(f"Input parameters - token_function_module: {token_function_module}, token_function: {token_function}")
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    raise ValueError(f"Token function not found: {token_function}")
                except Exception as e:
                    # Enhanced exception logging with traceback and input parameters
                    logger.error(f"Error calling token function at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
                    logger.error(f"Input parameters - token_function_module: {token_function_module}, token_function: {token_function}")
                    logger.error(f"Full traceback: {traceback.format_exc()}")
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
                    logger.info(f"VERTEXAI_CREDENTIALS_DEBUG: credentials type={type(credentials)}")
                    
                except ImportError as e:
                    # Enhanced exception logging with traceback and input parameters
                    logger.error(f"Failed to import credentials module at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
                    logger.error(f"Input parameters - credentials_function_module: {credentials_function_module}")
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    raise ValueError(f"Credentials function module not found: {credentials_function_module}")
                except AttributeError as e:
                    # Enhanced exception logging with traceback and input parameters
                    logger.error(f"Credentials function not found at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
                    logger.error(f"Input parameters - credentials_function_module: {credentials_function_module}, credentials_function: {credentials_function}")
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    raise ValueError(f"Credentials function not found: {credentials_function}")
                except Exception as e:
                    # Enhanced exception logging with traceback and input parameters
                    logger.error(f"Error calling credentials function at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
                    logger.error(f"Input parameters - credentials_function_module: {credentials_function_module}, credentials_function: {credentials_function}")
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    raise ValueError(f"Failed to get credentials from in-house function: {str(e)}")
            
            elif api_key:
                # Fallback to API key if no custom function is provided
                logger.info("Using API key for on-premise authentication")
                os.environ["GOOGLE_API_KEY"] = api_key
            
            # Set up transport configuration
            transport_params = {}
            if api_transport:
                logger.info(f"VERTEXAI_INIT_DEBUG [On-Premise]: Using api_transport={api_transport}")
                transport_params["api_transport"] = api_transport
                
                # Configure SSL for custom transports
                if api_transport == "rest" and not ssl_verify:
                    logger.info(f"VERTEXAI_SSL_DEBUG [On-Premise]: Configuring REST transport with SSL verification disabled")
                    # For REST transport, we can configure SSL through requests
                    import requests
                    from requests.adapters import HTTPAdapter
                    from urllib3.util.retry import Retry
                    
                    # Create a session with disabled SSL verification
                    session = requests.Session()
                    session.verify = False
                    
                    # Store the session for use by the REST transport
                    # Note: This is a workaround - actual implementation may vary
                    logger.info(f"VERTEXAI_SSL_DEBUG [On-Premise]: Created requests session with SSL verification disabled")
                
            else:
                logger.info(f"VERTEXAI_INIT_DEBUG [On-Premise]: No api_transport specified, using default")
            
            # Handle custom CA certificates
            if ssl_ca_cert_path:
                logger.info(f"VERTEXAI_SSL_DEBUG [On-Premise]: Using custom CA certificate: {ssl_ca_cert_path}")
                import os
                os.environ["REQUESTS_CA_BUNDLE"] = ssl_ca_cert_path
                os.environ["CURL_CA_BUNDLE"] = ssl_ca_cert_path
            
            # Incrementally build init_kwargs
            init_kwargs = {}
            init_kwargs["project"] = self.project_id
            init_kwargs["api_endpoint"] = endpoint_url
            init_kwargs.update(transport_params)
            if credentials:
                init_kwargs["credentials"] = credentials
            # Only add location if no custom endpoint is provided (for standard Google Cloud)
            if not endpoint_url:
                init_kwargs["location"] = self.location
                logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: Including location parameter for standard Google Cloud endpoint")
            else:
                logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: Skipping location parameter due to custom endpoint: {endpoint_url}")
                logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: Custom endpoints have location embedded in URL, location parameter not needed")
            
            # Initialize Vertex AI
            try:
                vertexai.init(**init_kwargs)
                self.model_client = GenerativeModel(self.model)
                logger.info("VERTEXAI_INIT_SUCCESS [On-Premise]: vertexai.init() completed successfully")
            except Exception as e:
                error_str = str(e)
                logger.error(f"VERTEXAI_INIT_ERROR [On-Premise]: Error during vertexai.init(): {error_str}")
                
                # Handle SSL certificate verification errors
                if "CERTIFICATE_VERIFY_FAILED" in error_str or "SSLCertVerificationError" in error_str:
                    logger.error(f"VERTEXAI_SSL_ERROR [On-Premise]: SSL certificate verification failed")
                    logger.error(f"VERTEXAI_SSL_ERROR [On-Premise]: This is common with self-signed or corporate certificates")
                    
                    if ssl_verify:
                        logger.warning(f"VERTEXAI_SSL_RETRY [On-Premise]: Retrying with SSL verification disabled...")
                        
                        # Disable SSL verification
                        import urllib3
                        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                        import os
                        os.environ["PYTHONHTTPSVERIFY"] = "0"
                        os.environ["CURL_CA_BUNDLE"] = ""
                        os.environ["REQUESTS_CA_BUNDLE"] = ""
                        
                        # Retry initialization
                        try:
                            vertexai.init(**init_kwargs)
                            self.model_client = GenerativeModel(self.model)
                            logger.warning("VERTEXAI_SSL_SUCCESS [On-Premise]: vertexai.init() succeeded with SSL verification disabled")
                            logger.warning("VERTEXAI_SSL_WARNING [On-Premise]: SSL verification is now disabled - this is insecure!")
                        except Exception as retry_e:
                            logger.error(f"VERTEXAI_SSL_RETRY_FAILED [On-Premise]: Retry with disabled SSL also failed: {str(retry_e)}")
                            raise retry_e
                    else:
                        logger.error(f"VERTEXAI_SSL_ERROR [On-Premise]: SSL verification already disabled, cannot retry")
                        raise e
                        
                # Handle other errors
                else:
                    logger.error(f"VERTEXAI_INIT_ERROR [On-Premise]: Unexpected error: {error_str}")
                    logger.error(f"VERTEXAI_INIT_ERROR [On-Premise]: Full parameters: {init_kwargs}")
                    raise e
            
        except Exception as e:
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"On-premise Vertex AI initialization failed at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
            logger.error(f"Input parameters - endpoint_url: {endpoint_url}, api_transport: {api_transport}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
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
            
            # Log detailed parameters before vertexai.init call
            corporate_init_params = {
                "project": self.project_id or "corporate-project",
                "api_endpoint": endpoint_url
            }
            
            # Only add location if no custom endpoint is provided (for standard Google Cloud)
            # Custom endpoints typically have location embedded in the URL
            if not endpoint_url:
                corporate_init_params["location"] = self.location or "corporate-location"
                logger.info(f"VERTEXAI_INIT_CALL [Corporate]: Including location parameter for standard Google Cloud endpoint")
            else:
                logger.info(f"VERTEXAI_INIT_CALL [Corporate]: Skipping location parameter due to custom endpoint: {endpoint_url}")
                logger.info(f"VERTEXAI_INIT_CALL [Corporate]: Custom endpoints have location embedded in URL, location parameter not needed")
            
            logger.info(f"VERTEXAI_INIT_CALL [Corporate]: Calling vertexai.init with parameters: {corporate_init_params}")
            logger.info(f"VERTEXAI_INIT_CALL [Corporate]: project={self.project_id or 'corporate-project'}, location={self.location or 'corporate-location' if not endpoint_url else 'SKIPPED_DUE_TO_CUSTOM_ENDPOINT'}, api_endpoint={endpoint_url}")
            logger.info(f"VERTEXAI_INIT_CALL [Corporate]: endpoint_url={endpoint_url}")
            logger.info(f"VERTEXAI_INIT_CALL [Corporate]: api_key={'SET' if api_key else 'NOT_SET'}")
            logger.info(f"VERTEXAI_INIT_CALL [Corporate]: auth_method={auth_method}")
            logger.info(f"VERTEXAI_INIT_CALL [Corporate]: deployment_type={self.deployment_type}")
            logger.info(f"VERTEXAI_INIT_CALL [Corporate]: model={self.model}")
            logger.info(f"VERTEXAI_INIT_CALL [Corporate]: credentials_path={self.credentials_path}")
            
            # Initialize with custom endpoint
            vertexai.init(**corporate_init_params)
            self.model_client = GenerativeModel(self.model)
            
        except Exception as e:
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"Corporate Vertex AI initialization failed at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
            logger.error(f"Input parameters - endpoint_url: {endpoint_url}, auth_method: {auth_method}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
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
        if self.api_transport == "rest":
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._generate_response_sync_impl, messages, tools, temperature, max_tokens, metadata)
        else:
            return await self._generate_response_async_impl(messages, tools, temperature, max_tokens, metadata)

    def _generate_response_sync_impl(self, messages, tools, temperature, max_tokens, metadata):
        try:
            logger.info(f"Vertex AI (REST) generate_response called with: messages={len(messages)}, tools={len(tools) if tools else 0}, temperature={temperature}, max_tokens={max_tokens}, metadata={metadata}")
            prompt = self._convert_messages_to_vertex_format(messages)
            generation_config = {"temperature": temperature}
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            vertex_tools = None
            if tools:
                if len(tools) > 1:
                    all_db_tools = all(any(keyword in t.get('function', {}).get('name', '').lower() for keyword in ['query', 'metrics', 'database', 'get_', 'search']) for t in tools)
                    if all_db_tools and len(tools) <= 3:
                        combined_description = f"Database tools available: {', '.join(t['function']['name'] for t in tools)}. "
                        combined_description += "Available operations: " + "; ".join(f"{t['function']['name']}: {t['function'].get('description', 'No description')}" for t in tools)
                        selected_tool = tools[0].copy()
                        selected_tool['function']['description'] = combined_description
                        tool_reason = f"enhanced tool '{selected_tool['function']['name']}' (representing {len(tools)} database tools)"
                    else:
                        db_tools = [t for t in tools if any(keyword in t.get('function', {}).get('name', '').lower() for keyword in ['query', 'metrics', 'database', 'get_', 'search'])]
                        if db_tools:
                            selected_tool = db_tools[0]
                            tool_reason = f"database tool '{selected_tool['function']['name']}'"
                        else:
                            selected_tool = tools[0]
                            tool_reason = f"first available tool '{selected_tool['function']['name']}'"
                    logger.info(f"Vertex AI limitation: Using {tool_reason} from {len(tools)} available tools")
                    tools = [selected_tool]
                vertex_tools = self._convert_tools_to_vertex_format(tools)
            request_metadata = {}
            if metadata:
                combined_metadata = {**settings.parsed_llm_metadata, **metadata}
                request_metadata.update(combined_metadata)
            elif settings.parsed_llm_metadata:
                request_metadata.update(settings.parsed_llm_metadata)
            request_kwargs = {"generation_config": generation_config}
            if vertex_tools:
                response = self.model_client.generate_content(prompt, tools=vertex_tools, **request_kwargs)
            else:
                response = self.model_client.generate_content(prompt, **request_kwargs)
            result = {"content": "", "tool_calls": []}
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
            if not result["tool_calls"]:
                try:
                    if hasattr(response, 'text') and response.text:
                        result["content"] = response.text
                except ValueError as text_error:
                    logger.warning(f"Cannot access response text: {str(text_error)}")
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'finish_reason'):
                            if candidate.finish_reason == "MALFORMED_FUNCTION_CALL":
                                result["content"] = "I encountered an issue with function calling. Let me help you in a different way."
                                logger.warning(f"MALFORMED_FUNCTION_CALL detected: {getattr(candidate, 'finish_message', 'Unknown reason')}")
                            else:
                                result["content"] = f"Response generation was stopped due to: {candidate.finish_reason}"
                        else:
                            result["content"] = "I'm unable to generate a response at the moment. Please try rephrasing your question."
                    else:
                        result["content"] = "I'm unable to generate a response at the moment. Please try again."
            return result
        except Exception as e:
            import traceback
            logger.error(f"Vertex AI (REST) response error: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    async def _generate_response_async_impl(self, messages, tools, temperature, max_tokens, metadata):
        try:
            logger.info(f"Vertex AI (gRPC) generate_response called with: messages={len(messages)}, tools={len(tools) if tools else 0}, temperature={temperature}, max_tokens={max_tokens}, metadata={metadata}")
            prompt = self._convert_messages_to_vertex_format(messages)
            generation_config = {"temperature": temperature}
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            vertex_tools = None
            if tools:
                if len(tools) > 1:
                    all_db_tools = all(any(keyword in t.get('function', {}).get('name', '').lower() for keyword in ['query', 'metrics', 'database', 'get_', 'search']) for t in tools)
                    if all_db_tools and len(tools) <= 3:
                        combined_description = f"Database tools available: {', '.join(t['function']['name'] for t in tools)}. "
                        combined_description += "Available operations: " + "; ".join(f"{t['function']['name']}: {t['function'].get('description', 'No description')}" for t in tools)
                        selected_tool = tools[0].copy()
                        selected_tool['function']['description'] = combined_description
                        tool_reason = f"enhanced tool '{selected_tool['function']['name']}' (representing {len(tools)} database tools)"
                    else:
                        db_tools = [t for t in tools if any(keyword in t.get('function', {}).get('name', '').lower() for keyword in ['query', 'metrics', 'database', 'get_', 'search'])]
                        if db_tools:
                            selected_tool = db_tools[0]
                            tool_reason = f"database tool '{selected_tool['function']['name']}'"
                        else:
                            selected_tool = tools[0]
                            tool_reason = f"first available tool '{selected_tool['function']['name']}'"
                    logger.info(f"Vertex AI limitation: Using {tool_reason} from {len(tools)} available tools")
                    tools = [selected_tool]
                vertex_tools = self._convert_tools_to_vertex_format(tools)
            request_metadata = {}
            if metadata:
                combined_metadata = {**settings.parsed_llm_metadata, **metadata}
                request_metadata.update(combined_metadata)
            elif settings.parsed_llm_metadata:
                request_metadata.update(settings.parsed_llm_metadata)
            request_kwargs = {"generation_config": generation_config}
            if vertex_tools:
                response = await self.model_client.generate_content_async(prompt, tools=vertex_tools, **request_kwargs)
            else:
                response = await self.model_client.generate_content_async(prompt, **request_kwargs)
            result = {"content": "", "tool_calls": []}
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
            if not result["tool_calls"]:
                try:
                    if hasattr(response, 'text') and response.text:
                        result["content"] = response.text
                except ValueError as text_error:
                    logger.warning(f"Cannot access response text: {str(text_error)}")
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'finish_reason'):
                            if candidate.finish_reason == "MALFORMED_FUNCTION_CALL":
                                result["content"] = "I encountered an issue with function calling. Let me help you in a different way."
                                logger.warning(f"MALFORMED_FUNCTION_CALL detected: {getattr(candidate, 'finish_message', 'Unknown reason')}")
                            else:
                                result["content"] = f"Response generation was stopped due to: {candidate.finish_reason}"
                        else:
                            result["content"] = "I'm unable to generate a response at the moment. Please try rephrasing your question."
                    else:
                        result["content"] = "I'm unable to generate a response at the moment. Please try again."
            return result
        except Exception as e:
            import traceback
            logger.error(f"Vertex AI (gRPC) response error: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    async def generate_embeddings(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> List[List[float]]:
        """Generate embeddings for the given texts using Vertex AI."""
        if self.api_transport == "rest":
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._generate_embeddings_sync_impl, texts, metadata)
        else:
            return await self._generate_embeddings_async_impl(texts, metadata)

    def _generate_embeddings_sync_impl(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> List[List[float]]:
        """Synchronous implementation for REST transport."""
        # (Copy the body of the old async generate_embeddings here, but use sync model methods)
        try:
            logger.info(f"Vertex AI (REST) generate_embeddings called with: texts={len(texts)}, metadata={metadata}")
            from vertexai.language_models import TextEmbeddingModel
            request_metadata = {}
            if metadata:
                combined_metadata = {**settings.parsed_llm_metadata, **metadata}
                request_metadata.update(combined_metadata)
            elif settings.parsed_llm_metadata:
                request_metadata.update(settings.parsed_llm_metadata)
            embedding_model_name = getattr(settings, 'embeddings_model', 'text-embedding-005')
            embedding_model = TextEmbeddingModel.from_pretrained(embedding_model_name)
            embeddings_list = []
            batch_size = 5
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = []
                for text in batch_texts:
                    try:
                        if embedding_model_name in ['text-embedding-004', 'text-embedding-005', 'gemini-embedding-001']:
                            embedding = embedding_model.get_embeddings([text], task_type="RETRIEVAL_DOCUMENT", metadata=request_metadata)
                        else:
                            embedding = embedding_model.get_embeddings([text], metadata=request_metadata)
                    except TypeError:
                        try:
                            embedding = embedding_model.get_embeddings([text], metadata=request_metadata)
                        except TypeError:
                            embedding = embedding_model.get_embeddings([text])
                    if hasattr(embedding[0], 'values'):
                        batch_embeddings.append(embedding[0].values)
                    else:
                        batch_embeddings.append(embedding[0])
                embeddings_list.extend(batch_embeddings)
            return embeddings_list
        except Exception as e:
            import traceback
            logger.error(f"Vertex AI (REST) embeddings error: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    async def _generate_embeddings_async_impl(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> List[List[float]]:
        """Async implementation for gRPC transport."""
        # (Move the current async body here)
        try:
            logger.info(f"Vertex AI (gRPC) generate_embeddings called with: texts={len(texts)}, metadata={metadata}")
            from vertexai.language_models import TextEmbeddingModel
            request_metadata = {}
            if metadata:
                combined_metadata = {**settings.parsed_llm_metadata, **metadata}
                request_metadata.update(combined_metadata)
            elif settings.parsed_llm_metadata:
                request_metadata.update(settings.parsed_llm_metadata)
            embedding_model_name = getattr(settings, 'embeddings_model', 'text-embedding-005')
            embedding_model = TextEmbeddingModel.from_pretrained(embedding_model_name)
            embeddings_list = []
            batch_size = 5
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = []
                for text in batch_texts:
                    try:
                        if embedding_model_name in ['text-embedding-004', 'text-embedding-005', 'gemini-embedding-001']:
                            embedding = await embedding_model.get_embeddings_async([text], task_type="RETRIEVAL_DOCUMENT", metadata=request_metadata)
                        else:
                            embedding = await embedding_model.get_embeddings_async([text], metadata=request_metadata)
                    except TypeError:
                        try:
                            embedding = await embedding_model.get_embeddings_async([text], metadata=request_metadata)
                        except TypeError:
                            embedding = await embedding_model.get_embeddings_async([text])
                    if hasattr(embedding[0], 'values'):
                        batch_embeddings.append(embedding[0].values)
                    else:
                        batch_embeddings.append(embedding[0])
                embeddings_list.extend(batch_embeddings)
            return embeddings_list
        except Exception as e:
            import traceback
            logger.error(f"Vertex AI (gRPC) embeddings error: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
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
            # Debug logging for api_transport from settings
            api_transport_value = getattr(settings, 'vertexai_api_transport', None)
            logger.info(f"VERTEXAI_CONFIG_DEBUG: Reading api_transport from settings")
            logger.info(f"VERTEXAI_CONFIG_DEBUG: settings.vertexai_api_transport={repr(api_transport_value)}")
            logger.info(f"VERTEXAI_CONFIG_DEBUG: api_transport type={type(api_transport_value)}")
            logger.info(f"VERTEXAI_CONFIG_DEBUG: api_transport bool={bool(api_transport_value)}")
            
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
                api_transport=api_transport_value,
                # SSL configuration
                ssl_verify=getattr(settings, 'vertexai_ssl_verify', True),
                ssl_ca_cert_path=getattr(settings, 'vertexai_ssl_ca_cert_path', None)
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