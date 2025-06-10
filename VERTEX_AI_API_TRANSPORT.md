# Vertex AI API Transport Configuration

## Overview

For on-premise Vertex AI deployments, you may need to specify a custom API transport method. This is typically required when your on-premise installation uses a specific transport protocol (e.g., REST vs gRPC).

## Configuration

### Environment Variable

Set the `VERTEXAI_API_TRANSPORT` environment variable:

```bash
# For REST transport
VERTEXAI_API_TRANSPORT=rest

# For gRPC transport  
VERTEXAI_API_TRANSPORT=grpc
```

### Complete On-Premise Configuration Example

```bash
# Basic on-premise configuration
LLM_PROVIDER=vertexai
VERTEXAI_DEPLOYMENT_TYPE=on_premise
VERTEXAI_PROJECT_ID=your_project_id
VERTEXAI_LOCATION=your_location
VERTEXAI_MODEL=gemini-2.0-flash-lite-001
VERTEXAI_ENDPOINT_URL=https://your-on-premise-endpoint.com

# Transport configuration
VERTEXAI_API_TRANSPORT=rest

# Authentication (choose one method)
VERTEXAI_API_KEY=your_api_key
# OR use in-house authentication functions
# VERTEXAI_TOKEN_FUNCTION=get_auth_token
# VERTEXAI_TOKEN_FUNCTION_MODULE=your_company.auth.gemini_auth
```

## How It Works

When `VERTEXAI_API_TRANSPORT` is set, the system will:

1. Load the transport configuration from the environment
2. Pass it to `vertexai.init()` as the `api_transport` parameter
3. Log the transport method being used for debugging

## Use Cases

- **REST Transport**: When your on-premise deployment only supports HTTP/REST APIs
- **gRPC Transport**: When your deployment uses gRPC for better performance
- **Custom Protocols**: Any other transport method supported by your on-premise installation

## Debugging

The application will log when custom API transport is being used:

```
INFO - Initializing Vertex AI with custom API transport: rest
```

This helps verify that your transport configuration is being applied correctly.

## Related Configuration

- `VERTEXAI_ENDPOINT_URL` - The custom endpoint for your on-premise deployment
- `VERTEXAI_API_KEY` - API key for authentication
- `VERTEXAI_TOKEN_FUNCTION` - In-house token generation function
- `VERTEXAI_CREDENTIALS_FUNCTION` - In-house credentials generation function 