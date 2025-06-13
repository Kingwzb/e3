#!/usr/bin/env python3
"""
Test script to verify VertexAIClient async interface works for both REST and gRPC transports.
"""
import asyncio
from app.core.llm import LLMClientConfig, VertexAIClient

async def test_vertexai_transport(api_transport):
    print(f"\n=== Testing VertexAIClient with api_transport='{api_transport}' ===")
    config = LLMClientConfig(
        provider="vertexai",
        model="gemini-pro",
        deployment_type="on_premise",
        endpoint_url="https://test-endpoint.company.com",
        api_transport=api_transport
    )
    client = VertexAIClient(config)
    # Test generate_embeddings
    texts = ["Hello world!", "How does Vertex AI handle REST vs gRPC?"]
    embeddings = await client.generate_embeddings(texts)
    print(f"Embeddings shape: {len(embeddings)} x {len(embeddings[0]) if embeddings else 0}")
    # Test generate_response
    messages = [
        {"role": "user", "content": "What is the difference between REST and gRPC in Vertex AI?"}
    ]
    response = await client.generate_response(messages)
    print(f"Response: {response['content'][:200]}{'...' if len(response['content']) > 200 else ''}")

if __name__ == "__main__":
    asyncio.run(test_vertexai_transport("rest"))
    asyncio.run(test_vertexai_transport("grpc")) 