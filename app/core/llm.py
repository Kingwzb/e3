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
            
            # Initialize Vertex AI with custom endpoint and credentials
            init_kwargs = {
                "project": self.project_id,
                "api_endpoint": endpoint_url
            }
            
            # Only add location if no custom endpoint is provided (for standard Google Cloud)
            # Custom endpoints typically have location embedded in the URL
            if not endpoint_url:
                init_kwargs["location"] = self.location
                logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: Including location parameter for standard Google Cloud endpoint")
            else:
                logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: Skipping location parameter due to custom endpoint: {endpoint_url}")
                logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: Custom endpoints have location embedded in URL, location parameter not needed")
            
            if credentials:
                # Add credentials to initialization parameters
                init_kwargs["credentials"] = credentials
                logger.info("Initializing Vertex AI with custom credentials")
                logger.info(f"VERTEXAI_INIT_DEBUG [On-Premise]: credentials type={type(credentials).__name__ if credentials else None}")
            else:
                logger.info(f"VERTEXAI_INIT_DEBUG [On-Premise]: No credentials provided")
            
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
            
            # Log detailed parameters before vertexai.init call
            logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: Complete initialization parameters:")
            logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: project={self.project_id}")
            logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: endpoint_url={endpoint_url}")
            logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: credentials={type(credentials).__name__ if credentials else None}")
            logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: api_key={'***SET***' if api_key else None}")
            logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: auth_method={auth_method}")
            logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: token_function={type(token_function).__name__ if token_function else None}")
            logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: api_transport={api_transport}")
            logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: ssl_verify={ssl_verify}")
            logger.info(f"VERTEXAI_INIT_CALL [On-Premise]: ssl_ca_cert_path={ssl_ca_cert_path}")
            
            # Combine all initialization parameters
            init_kwargs = {
                "project": self.project_id,
                "api_endpoint": endpoint_url,  # Note: it's api_endpoint for custom endpoints
                **transport_params
            }
            
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
        """Generate a response using Vertex AI API."""
        try:
            # Log input parameters for debugging
            logger.info(f"Vertex AI generate_response called with: messages={len(messages)}, tools={len(tools) if tools else 0}, temperature={temperature}, max_tokens={max_tokens}, metadata={list(metadata.keys()) if metadata else 'None'}")
            
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
            if not result["tool_calls"]:
                try:
                    if hasattr(response, 'text') and response.text:
                        result["content"] = response.text
                except ValueError as text_error:
                    # Handle cases where response.text is not available (e.g., MALFORMED_FUNCTION_CALL)
                    logger.warning(f"Cannot access response text: {str(text_error)}")
                    # Check if we have any candidate with finish_reason
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
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"Vertex AI API error at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
            logger.error(f"Input parameters - messages: {len(messages)} items, tools: {len(tools) if tools else 0}, temperature: {temperature}, max_tokens: {max_tokens}, metadata: {list(metadata.keys()) if metadata else 'None'}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise Exception(f"Vertex AI LLM generation failed: {str(e)}")
    
    async def generate_embeddings(self, texts: List[str], metadata: Optional[Dict[str, Any]] = None) -> List[List[float]]:
        """Generate embeddings for the given texts using Vertex AI."""
        try:
            # Log input parameters for debugging with complete values
            logger.info(f"Vertex AI generate_embeddings called with: texts={len(texts)}, metadata={metadata}")
            logger.info(f"GENERATE_EMBEDDINGS_INPUT: texts_preview={[text[:100] + '...' if len(text) > 100 else text for text in texts[:3]]}")
            logger.info(f"GENERATE_EMBEDDINGS_INPUT: complete_metadata={metadata}")
            logger.info(f"GENERATE_EMBEDDINGS_INPUT: global_metadata={settings.parsed_llm_metadata}")
            logger.info(f"GENERATE_EMBEDDINGS_INPUT: total_texts_count={len(texts)}")
            
            from vertexai.language_models import TextEmbeddingModel
            
            # Handle metadata for Vertex AI embedding requests
            request_metadata = {}
            if metadata:
                # Merge global metadata with call-specific metadata
                combined_metadata = {**settings.parsed_llm_metadata, **metadata}
                request_metadata.update(combined_metadata)
                logger.info(f"Adding metadata to Vertex AI embeddings request: {combined_metadata}")
                logger.info(f"METADATA_MERGE: global_metadata={settings.parsed_llm_metadata}")
                logger.info(f"METADATA_MERGE: call_metadata={metadata}")
                logger.info(f"METADATA_MERGE: combined_metadata={combined_metadata}")
            elif settings.parsed_llm_metadata:
                request_metadata.update(settings.parsed_llm_metadata)
                logger.info(f"Adding global metadata to Vertex AI embeddings request: {settings.parsed_llm_metadata}")
                logger.info(f"METADATA_GLOBAL: global_metadata={settings.parsed_llm_metadata}")
            
            # Get the embedding model name from settings
            embedding_model_name = getattr(settings, 'embeddings_model', 'text-embedding-005')
            logger.info(f"EMBEDDING_MODEL_CONFIG: model_name={embedding_model_name}")
            logger.info(f"EMBEDDING_MODEL_CONFIG: final_request_metadata={request_metadata}")
            
            # Initialize the embedding model - it will use the transport from vertexai.init()
            embedding_model = TextEmbeddingModel.from_pretrained(embedding_model_name)
            
            # Generate embeddings for all texts
            embeddings_list = []
            
            # Process texts in batches to avoid API limits
            batch_size = 5
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # Generate embeddings for this batch
                batch_embeddings = []
                for text in batch_texts:
                    # Generate embeddings (task_type may not be supported in all versions)
                    try:
                        # Try with task_type first for newer models and pass metadata
                        if embedding_model_name in ['text-embedding-004', 'text-embedding-005', 'gemini-embedding-001']:
                            # Log detailed parameters before get_embeddings call
                            get_embeddings_params = {
                                "texts": [text],
                                "task_type": "RETRIEVAL_DOCUMENT",
                                "metadata": request_metadata
                            }
                            logger.info(f"GET_EMBEDDINGS_CALL [With Task Type]: Calling get_embeddings with parameters: {get_embeddings_params}")
                            logger.info(f"GET_EMBEDDINGS_CALL [With Task Type]: texts=['{text[:50]}...'], task_type='RETRIEVAL_DOCUMENT', metadata={request_metadata}")
                            logger.info(f"GET_EMBEDDINGS_CALL [With Task Type]: embedding_model_name={embedding_model_name}")
                            logger.info(f"GET_EMBEDDINGS_CALL [With Task Type]: text_length={len(text)}, batch_size={batch_size}, batch_index={i//batch_size}")
                            
                            embedding = embedding_model.get_embeddings([text], task_type="RETRIEVAL_DOCUMENT", metadata=request_metadata)
                        else:
                            # Log detailed parameters before get_embeddings call
                            get_embeddings_params = {
                                "texts": [text],
                                "metadata": request_metadata
                            }
                            logger.info(f"GET_EMBEDDINGS_CALL [With Metadata]: Calling get_embeddings with parameters: {get_embeddings_params}")
                            logger.info(f"GET_EMBEDDINGS_CALL [With Metadata]: texts=['{text[:50]}...'], metadata={request_metadata}")
                            logger.info(f"GET_EMBEDDINGS_CALL [With Metadata]: embedding_model_name={embedding_model_name}")
                            logger.info(f"GET_EMBEDDINGS_CALL [With Metadata]: text_length={len(text)}, batch_size={batch_size}, batch_index={i//batch_size}")
                            
                            embedding = embedding_model.get_embeddings([text], metadata=request_metadata)
                    except TypeError:
                        # Fallback if task_type or metadata is not supported
                        try:
                            # Log detailed parameters before get_embeddings call
                            get_embeddings_params = {
                                "texts": [text],
                                "metadata": request_metadata
                            }
                            logger.info(f"GET_EMBEDDINGS_CALL [Fallback With Metadata]: Calling get_embeddings with parameters: {get_embeddings_params}")
                            logger.info(f"GET_EMBEDDINGS_CALL [Fallback With Metadata]: texts=['{text[:50]}...'], metadata={request_metadata}")
                            logger.info(f"GET_EMBEDDINGS_CALL [Fallback With Metadata]: embedding_model_name={embedding_model_name}")
                            logger.info(f"GET_EMBEDDINGS_CALL [Fallback With Metadata]: text_length={len(text)}, batch_size={batch_size}, batch_index={i//batch_size}")
                            
                            embedding = embedding_model.get_embeddings([text], metadata=request_metadata)
                        except TypeError:
                            # Final fallback without metadata if not supported
                            # Log detailed parameters before get_embeddings call
                            get_embeddings_params = {
                                "texts": [text]
                            }
                            logger.info(f"GET_EMBEDDINGS_CALL [Final Fallback]: Calling get_embeddings with parameters: {get_embeddings_params}")
                            logger.info(f"GET_EMBEDDINGS_CALL [Final Fallback]: texts=['{text[:50]}...'], no_metadata=True")
                            logger.info(f"GET_EMBEDDINGS_CALL [Final Fallback]: embedding_model_name={embedding_model_name}")
                            logger.info(f"GET_EMBEDDINGS_CALL [Final Fallback]: text_length={len(text)}, batch_size={batch_size}, batch_index={i//batch_size}")
                            
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
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"Vertex AI language models not available at line {traceback.extract_tb(sys.exc_info()[2])[-1].lineno}")
            logger.error(f"Input parameters - texts: {len(texts)}, metadata: {metadata}")
            logger.error(f"Text samples: {[text[:100] + '...' if len(text) > 100 else text for text in texts[:2]]}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise Exception("Vertex AI embedding generation failed: Missing dependencies")
        except Exception as e:
            # Enhanced exception logging with traceback and input parameters
            logger.error(f"Vertex AI embeddings error at line {traceback.extract_tb(e.__traceback__)[-1].lineno}: {str(e)}")
            logger.error(f"Input parameters - texts: {len(texts)}, metadata: {metadata}")
            logger.error(f"Text samples: {[text[:100] + '...' if len(text) > 100 else text for text in texts[:2]]}")
            logger.error(f"Embedding model: {getattr(settings, 'embeddings_model', 'text-embedding-005')}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
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