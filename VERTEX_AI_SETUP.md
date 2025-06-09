# Google Vertex AI Setup Guide

This guide will help you configure Google Vertex AI as your LLM provider for the AI Chat Agent.

## Prerequisites

1. **Google Cloud Project**: You need an active Google Cloud Project with billing enabled
2. **Vertex AI API**: Enable the Vertex AI API in your project
3. **Authentication**: Set up service account credentials

## Step 1: Enable Vertex AI API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project or create a new one
3. Navigate to **APIs & Services** > **Library**
4. Search for "Vertex AI API" and enable it
5. Also enable "AI Platform API" if not already enabled

## Step 2: Create Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Provide a name (e.g., "ai-chat-agent-vertexai")
4. Add description: "Service account for AI Chat Agent Vertex AI access"
5. Click **Create and Continue**

## Step 3: Assign Roles

Assign the following roles to your service account:

- **Vertex AI User** (`roles/aiplatform.user`)
- **ML Developer** (`roles/ml.developer`) - Optional, for advanced features

## Step 4: Create and Download Key

1. Click on your newly created service account
2. Go to the **Keys** tab
3. Click **Add Key** > **Create new key**
4. Choose **JSON** format
5. Download the key file and save it securely

## Step 5: Configure Environment Variables

Update your `.env` file with the following configuration:

### For Google Cloud Vertex AI (Default)

```bash
# LLM Provider Configuration
LLM_PROVIDER=vertexai

# Google Vertex AI Configuration
VERTEXAI_PROJECT_ID=your-gcp-project-id
VERTEXAI_LOCATION=us-central1
VERTEXAI_MODEL=gemini-2.0-flash-lite-001
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# Deployment Type (default: cloud)
VERTEXAI_DEPLOYMENT_TYPE=cloud
```

### For Corporate/On-Premise Hosted Gemini

```bash
# LLM Provider Configuration
LLM_PROVIDER=vertexai

# Corporate Vertex AI Configuration
VERTEXAI_PROJECT_ID=your-corporate-project-id
VERTEXAI_LOCATION=corporate-location
VERTEXAI_MODEL=gemini-2.0-flash-lite-001

# Corporate Deployment Configuration
VERTEXAI_DEPLOYMENT_TYPE=corporate
VERTEXAI_ENDPOINT_URL=https://your-corporate-gemini-endpoint.com/v1
VERTEXAI_API_KEY=your_corporate_api_key
VERTEXAI_AUTH_METHOD=api_key
```

### For On-Premise Vertex AI

**Basic On-Premise Configuration:**
```bash
# LLM Provider Configuration
LLM_PROVIDER=vertexai

# On-Premise Vertex AI Configuration
VERTEXAI_PROJECT_ID=your-onprem-project-id
VERTEXAI_LOCATION=onprem-location
VERTEXAI_MODEL=gemini-2.0-flash-lite-001

# On-Premise Deployment Configuration
VERTEXAI_DEPLOYMENT_TYPE=on_premise
VERTEXAI_ENDPOINT_URL=https://your-onprem-vertex-endpoint.com
VERTEXAI_API_KEY=your_onprem_api_key
```

**On-Premise with In-House Authentication Library:**
```bash
# LLM Provider Configuration
LLM_PROVIDER=vertexai

# On-Premise Vertex AI Configuration
VERTEXAI_PROJECT_ID=your-onprem-project-id
VERTEXAI_LOCATION=onprem-location
VERTEXAI_MODEL=gemini-2.0-flash-lite-001

# On-Premise Deployment Configuration
VERTEXAI_DEPLOYMENT_TYPE=on_premise
VERTEXAI_ENDPOINT_URL=https://your-onprem-vertex-endpoint.com

# Option 1: Token function (returns a string token)
VERTEXAI_TOKEN_FUNCTION=get_auth_token
VERTEXAI_TOKEN_FUNCTION_MODULE=your_company.auth.gemini_auth

# Option 2: Credentials function (returns credentials object)
# VERTEXAI_CREDENTIALS_FUNCTION=get_gemini_credentials
# VERTEXAI_CREDENTIALS_FUNCTION_MODULE=your_company.auth.vertex_auth
```

### Available Models

Choose from these Vertex AI models:

- `gemini-2.0-flash-lite-001` - Latest lightweight model (recommended)
- `gemini-1.5-pro-002` - Most capable model
- `gemini-1.5-flash-002` - Faster, optimized for speed
- `gemini-1.0-pro-001` - Previous generation model

### Available Locations

Common Vertex AI locations:

- `us-central1` (Iowa)
- `us-east1` (South Carolina)
- `us-west1` (Oregon)
- `europe-west1` (Belgium)
- `asia-southeast1` (Singapore)

### Deployment Types

The system supports three deployment types for Vertex AI:

1. **`cloud`** (Default) - Google Cloud Vertex AI
   - Uses standard Google Cloud authentication
   - Requires service account credentials
   - Full feature support

2. **`corporate`** - Corporate hosted Gemini models
   - Uses custom endpoint URL
   - API key authentication
   - Suitable for enterprise deployments

3. **`on_premise`** - On-premise Vertex AI deployment
   - Custom endpoint configuration
   - Flexible authentication methods
   - Support for in-house authentication libraries
   - For private cloud deployments

## Step 6: Creating In-House Authentication Functions (On-Premise Only)

For on-premise deployments using in-house authentication libraries, you need to create functions that return authentication tokens or credentials.

### Option 1: Token Function

Create a function that returns a string token:

```python
# your_company/auth/gemini_auth.py

def get_auth_token():
    """
    Get authentication token for on-premise Gemini.
    
    Returns:
        str: Authentication token
    """
    # Your in-house authentication logic here
    # This might involve calling internal APIs, reading from secure storage, etc.
    
    # Example implementation:
    import requests
    
    response = requests.post(
        "https://internal-auth.company.com/api/tokens",
        headers={"Authorization": "Bearer your-service-token"},
        json={"service": "gemini", "scope": "vertex-ai"}
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to get token: {response.status_code}")
```

### Option 2: Credentials Function

Create a function that returns a Google credentials object:

```python
# your_company/auth/vertex_auth.py

from google.oauth2 import credentials as oauth2_credentials

def get_gemini_credentials():
    """
    Get Google credentials for on-premise Vertex AI.
    
    Returns:
        google.oauth2.credentials.Credentials: Credentials object
    """
    # Your in-house authentication logic here
    
    # Example implementation:
    token = get_token_from_internal_service()
    
    # Create credentials object
    creds = oauth2_credentials.Credentials(
        token=token,
        # Add other required fields as needed
        # refresh_token=refresh_token,
        # token_uri="https://oauth2.googleapis.com/token",
        # client_id=client_id,
        # client_secret=client_secret
    )
    
    return creds

def get_token_from_internal_service():
    """Helper function to get token from internal service."""
    # Your internal token retrieval logic
    pass
```

### Authentication Function Requirements

Your authentication functions should:

1. **Be importable**: The module path should be accessible from your Python environment
2. **Handle errors gracefully**: Raise clear exceptions if authentication fails
3. **Return appropriate types**: 
   - Token functions should return a string
   - Credentials functions should return a `google.oauth2.credentials.Credentials` object
4. **Be secure**: Follow your organization's security best practices
5. **Be reliable**: Include retry logic and error handling as needed

## Step 7: Install Dependencies

Make sure you have the required dependencies installed:

```bash
pip install google-cloud-aiplatform google-auth google-auth-oauthlib google-auth-httplib2
```

Or if using the project's requirements:

```bash
pip install -r requirements.txt
```

## Step 8: Test Configuration

Run the test script to verify your configuration:

```bash
python test_llm_providers.py
```

Or test via the API:

```bash
# Start the application
python start.py

# Test Vertex AI connectivity
curl -X POST "http://localhost:8000/api/llm/test" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Vertex AI!"}'
```

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   DefaultCredentialsError: Could not automatically determine credentials
   ```
   **Solution**: Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service account key file.

2. **Permission Denied**
   ```
   403 Forbidden: The caller does not have permission
   ```
   **Solution**: Verify your service account has the correct roles assigned.

3. **Project Not Found**
   ```
   404 Not Found: The project was not found
   ```
   **Solution**: Check that `VERTEXAI_PROJECT_ID` matches your actual GCP project ID.

4. **Model Not Available**
   ```
   Model not found in location
   ```
   **Solution**: Verify the model is available in your chosen location. Try `us-central1` which has the most models.

### Debug Steps

1. **Verify Project ID**:
   ```bash
   gcloud config get-value project
   ```

2. **Test Authentication**:
   ```bash
   gcloud auth application-default login
   ```

3. **List Available Models**:
   ```bash
   gcloud ai models list --region=us-central1
   ```

## Security Best Practices

1. **Service Account Key Security**:
   - Store the key file in a secure location
   - Never commit the key file to version control
   - Use environment variables for the file path
   - Consider using Google Cloud's metadata service in production

2. **Minimal Permissions**:
   - Only assign necessary roles to the service account
   - Regularly review and audit permissions

3. **Key Rotation**:
   - Rotate service account keys regularly
   - Monitor key usage in Cloud Console

## Cost Considerations

- Vertex AI charges per request and token usage
- Monitor usage in the Google Cloud Console
- Set up billing alerts to avoid unexpected charges
- Consider using `gemini-1.5-flash` for cost optimization

## Production Deployment

For production environments:

1. **Use Workload Identity** instead of service account keys when running on Google Cloud
2. **Set up monitoring** for API usage and costs
3. **Configure rate limiting** to control usage
4. **Use VPC Service Controls** for additional security

## Support

- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Gemini API Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [Google Cloud Support](https://cloud.google.com/support) 