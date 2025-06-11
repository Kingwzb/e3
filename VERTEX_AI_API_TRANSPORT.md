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

### Transport Configuration

The system handles API transport configuration for different deployment scenarios:

- **Default**: If no `api_transport` is specified, Vertex AI uses its default transport
- **`rest`**: Explicitly sets REST/HTTP transport by passing `api_transport="rest"` to `vertexai.init()`
- **`grpc`**: Explicitly sets gRPC transport by passing `api_transport="grpc"` to `vertexai.init()`
- **Other values**: Passed directly to `vertexai.init()` as the `api_transport` parameter

#### Transport Parameter Logic

| VERTEXAI_API_TRANSPORT Value | Passed to vertexai.init() | Use Case |
|------------------------------|---------------------------|----------|
| Not set or empty | No transport parameter | Default Vertex AI transport |
| `rest` | `api_transport="rest"` | Explicit REST/HTTP transport |
| `grpc` | `api_transport="grpc"` | Explicit gRPC transport |
| Custom value | `api_transport=custom_value` | Custom transport configuration |

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

## Parameter Handling for Custom Endpoints

### Location Parameter Behavior

When using custom Vertex AI endpoints (on-premise or corporate deployments), the `location` parameter is automatically omitted from the `vertexai.init()` call because:

1. **Custom endpoints embed location information** in the URL itself
2. **Passing location with custom endpoints** can cause conflicts or errors
3. **Standard Google Cloud endpoints** require the location parameter for regional routing

#### Automatic Location Parameter Logic

| Deployment Type | Endpoint Type | Location Parameter | Reason |
|----------------|---------------|-------------------|---------|
| `cloud` | Default Google Cloud | ✅ **Included** | Required for regional routing |
| `on_premise` | Custom URL provided | ❌ **Skipped** | Location embedded in custom URL |
| `corporate` | Custom URL provided | ❌ **Skipped** | Location embedded in custom URL |
| `on_premise` | No custom URL | ✅ **Included** | Falls back to standard Google Cloud |

#### Example Configurations

**Standard Google Cloud (location included):**
```bash
VERTEXAI_DEPLOYMENT_TYPE=cloud
VERTEXAI_PROJECT_ID=my-project
VERTEXAI_LOCATION=us-central1
# No VERTEXAI_ENDPOINT_URL
```

**Custom Endpoint (location skipped):**
```bash
VERTEXAI_DEPLOYMENT_TYPE=on_premise
VERTEXAI_PROJECT_ID=my-project
VERTEXAI_LOCATION=us-central1  # Used for config but not passed to vertexai.init()
VERTEXAI_ENDPOINT_URL=https://my-company-vertex.internal.com/v1
```

The logging will clearly indicate when the location parameter is included or skipped:
```
VERTEXAI_INIT_CALL [On-Premise]: Skipping location parameter due to custom endpoint: https://my-company-vertex.internal.com/v1
VERTEXAI_INIT_CALL [On-Premise]: Custom endpoints have location embedded in URL, location parameter not needed
``` 