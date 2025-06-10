# Vertex AI API Transport Configuration

## Overview

For on-premise Vertex AI deployments, you may need to specify a custom API transport method. This is typically required when your on-premise installation uses a specific transport protocol (e.g., REST vs gRPC).

## Configuration

### Environment Variable

Set the `VERTEXAI_API_TRANSPORT` environment variable:

```bash
# For REST transport (uses default HTTP transport)
VERTEXAI_API_TRANSPORT=rest

# For gRPC transport (explicitly sets gRPC transport)
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
2. Handle the transport configuration appropriately:
   - **REST**: Uses default HTTP transport (does not pass api_transport parameter)
   - **gRPC**: Explicitly sets gRPC transport via `vertexai.init()`
   - **Other**: Passes the value directly to `vertexai.init()`
3. Log the transport method being used for debugging

## Use Cases

- **REST Transport**: When your on-premise deployment only supports HTTP/REST APIs (uses default HTTP transport)
- **gRPC Transport**: When your deployment uses gRPC for better performance
- **Custom Protocols**: Any other transport method supported by your on-premise installation

## Transport Handling Details

- **`rest`**: Uses the default HTTP/REST transport. The system does not pass the `api_transport` parameter to `vertexai.init()`, allowing Vertex AI to use its default REST transport.
- **`grpc`**: Explicitly sets gRPC transport by passing `api_transport="grpc"` to `vertexai.init()`.
- **Other values**: Passed directly to `vertexai.init()` as the `api_transport` parameter.

## Debugging

The application will log when API transport configuration is being applied:

```
# For REST transport
INFO - Using REST transport for Vertex AI (api_transport=None)

# For gRPC transport  
INFO - Initializing Vertex AI with gRPC transport: grpc

# For other transports
INFO - Initializing Vertex AI with custom API transport: custom_value
```

This helps verify that your transport configuration is being applied correctly.

## Related Configuration

- `VERTEXAI_ENDPOINT_URL` - The custom endpoint for your on-premise deployment
- `VERTEXAI_API_KEY` - API key for authentication
- `VERTEXAI_TOKEN_FUNCTION` - In-house token generation function
- `VERTEXAI_CREDENTIALS_FUNCTION` - In-house credentials generation function 