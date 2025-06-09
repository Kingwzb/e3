# Migration from sentence-transformers to Vertex AI Embeddings

This guide explains how to migrate from the blocked `all-MiniLM-L6-v2` model (sentence-transformers) to Google Vertex AI embedding models for corporate firewall environments.

## Overview

The original implementation used the `all-MiniLM-L6-v2` model from Hugging Face via the `sentence-transformers` library. This model requires downloading from external sources, which is blocked by corporate firewalls. The solution is to use Google Vertex AI's embedding models instead.

## Changes Made

### 1. Configuration Updates

**File: `app/core/config.py`**
- Changed default embedding model from `all-MiniLM-L6-v2` to `text-embedding-005`

**File: `env.example`**
- Updated the example embedding model configuration

### 2. Vector Store Implementation

**File: `app/tools/vector_store.py`**
- Replaced `sentence-transformers` dependency with Vertex AI client
- Updated embedding generation to use Vertex AI API
- Added async/sync wrapper for embedding generation
- Updated dimension from 384 (MiniLM) to 768 (Vertex AI models)

### 3. LLM Client Enhancement

**File: `app/core/llm.py`**
- Implemented proper `generate_embeddings` method for `VertexAIClient`
- Added support for different Vertex AI embedding models
- Added batch processing for rate limit compliance
- Removed sentence-transformers fallback

### 4. Dependencies

**File: `requirements.txt`**
- Removed `sentence-transformers>=2.2.0` dependency
- Kept `google-cloud-aiplatform>=1.38.0` for Vertex AI support

## Available Vertex AI Embedding Models

### Latest Models (Recommended)
- `text-embedding-005` - Latest general-purpose model (768 dimensions)
- `gemini-embedding-001` - Latest Gemini-based embedding model (768 dimensions)  
- `text-multilingual-embedding-002` - For multilingual use cases (768 dimensions)

### Legacy Models (Still Supported)
- `text-embedding-004` - Previous version (768 dimensions)

## Configuration

### Environment Variables

Set these in your `.env` file:

```bash
# Use Vertex AI as the LLM provider
LLM_PROVIDER=vertexai

# Vertex AI Configuration
VERTEXAI_PROJECT_ID=your-gcp-project-id
VERTEXAI_LOCATION=us-central1
VERTEXAI_MODEL=gemini-2.0-flash-lite-001
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json

# Embedding Model Configuration
EMBEDDING_MODEL=text-embedding-005

# For corporate/on-premise deployments
VERTEXAI_DEPLOYMENT_TYPE=cloud  # or "corporate" or "on_premise"
# VERTEXAI_ENDPOINT_URL=https://your-corporate-endpoint.com/v1
# VERTEXAI_API_KEY=your_corporate_api_key
```

### Authentication Options

#### Option 1: Service Account Key (Recommended for Development)
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

#### Option 2: Corporate Endpoint with API Key
```bash
VERTEXAI_DEPLOYMENT_TYPE=corporate
VERTEXAI_ENDPOINT_URL=https://your-corporate-vertex-endpoint.com
VERTEXAI_API_KEY=your_corporate_api_key
```

#### Option 3: On-Premise with Custom Authentication
```bash
VERTEXAI_DEPLOYMENT_TYPE=on_premise
VERTEXAI_ENDPOINT_URL=https://your-onprem-endpoint.com
VERTEXAI_TOKEN_FUNCTION=get_auth_token
VERTEXAI_TOKEN_FUNCTION_MODULE=your_company.auth.vertex_auth
```

## Testing the Migration

Run the test script to verify everything works:

```bash
python test_vertex_embeddings.py
```

This script will:
1. Verify Vertex AI client initialization
2. Test embedding generation
3. Test vector store functionality
4. Verify search capabilities

## Benefits of Migration

1. **Firewall Compatibility**: No external downloads required
2. **Enterprise Support**: Backed by Google Cloud enterprise SLA
3. **Better Performance**: State-of-the-art embedding models
4. **Scalability**: Cloud-native with automatic scaling
5. **Security**: Runs within your VPC/corporate network
6. **Cost Efficiency**: Pay-per-use pricing model

## Model Performance Comparison

| Model | Dimension | MTEB Score | Use Case |
|-------|-----------|------------|----------|
| all-MiniLM-L6-v2 (old) | 384 | ~59% | General purpose |
| text-embedding-005 | 768 | ~66% | General purpose |
| gemini-embedding-001 | 768 | ~66%+ | Latest Gemini model |

## Migration Checklist

- [ ] Update `.env` file with Vertex AI configuration
- [ ] Set up Vertex AI authentication (service account or corporate)
- [ ] Update embedding model to `text-embedding-005` or `gemini-embedding-001`
- [ ] Run test script to verify functionality
- [ ] Clear old FAISS index (optional, for dimension compatibility)
- [ ] Test end-to-end application functionality

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure GOOGLE_APPLICATION_CREDENTIALS path is correct
   - Verify service account has Vertex AI permissions
   - Check project ID and location settings

2. **Rate Limiting**
   - The implementation includes built-in batch processing
   - Adjust batch size if needed (currently set to 5)

3. **Dimension Mismatch**
   - Clear existing FAISS index: `rm -rf data/faiss_index/*`
   - Restart application to rebuild with 768 dimensions

4. **Corporate Firewall Issues**
   - Ensure Vertex AI endpoints are whitelisted
   - Use corporate deployment type with internal endpoints
   - Verify DNS resolution for Google Cloud APIs

### Getting Help

If you encounter issues:
1. Check the logs for detailed error messages
2. Verify your Vertex AI project setup and permissions
3. Test authentication separately using `gcloud auth list`
4. Consult the Vertex AI documentation for your deployment type

## Next Steps

After successful migration:
1. Monitor embedding quality and search relevance
2. Consider tuning embedding models for your specific use case
3. Implement caching for frequently used embeddings
4. Set up monitoring and alerting for Vertex AI usage 