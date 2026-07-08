#!/usr/bin/env python3
"""
Test script for verifying configuration and calls of different model platforms
"""

import json
import os
import sys
from model_manager import model_manager


def test_llm_provider(provider: str, model: str):
    """Test LLM provider"""
    print(f"\nTesting LLM Provider: {provider}, Model: {model}")
    print("=" * 50)

    try:
        client = model_manager.get_llm_client(provider)
        print(f"✓ LLM client initialized successfully")

        # Test simple conversation
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": "Hello! Please respond with 'Test successful'",
                },
            ],
            temperature=0.0,
            max_tokens=50,
        )

        result = response.choices[0].message.content
        print(f"✓ LLM call successful: {result}")

    except Exception as e:
        print(f"✗ LLM test failed: {e}")


def test_embedding_provider(provider: str):
    """Test embedding model provider"""
    print(f"\nTesting Embedding Provider: {provider}")
    print("=" * 50)

    try:
        model = model_manager.get_embedding_model(provider)
        print(f"✓ Embedding model initialized successfully")

        # Test embedding generation
        test_text = "This is a test sentence for embedding."
        embedding = model.encode(test_text)

        if isinstance(embedding, dict) and "dense_vecs" in embedding:
            embedding = embedding["dense_vecs"]

        print(
            f"✓ Embedding generated successfully, dimension: {len(embedding) if hasattr(embedding, '__len__') else 'N/A'}"
        )

    except Exception as e:
        print(f"✗ Embedding model test failed: {e}")


def print_available_providers():
    """Print available providers"""
    print("\nAvailable LLM providers:")
    for provider in model_manager.get_available_providers():
        models = model_manager.get_available_models(provider)
        print(f"  - {provider}: {models}")

    print("\nAvailable embedding model providers:")
    for provider in model_manager.get_available_embedding_providers():
        print(f"  - {provider}")


def main():
    """Main function"""
    print("Model Manager Test Script")
    print("=" * 50)

    # Print configuration info
    print_available_providers()

    # Print default configuration
    defaults = model_manager.get_default_config()
    print(f"\nDefault configuration: {defaults}")

    # Test each provider
    test_cases = [
        # LLM tests
        ("local_api", "qwen2.5-14b-instruct"),
        ("lmstudio", "gemma-3-270m-it"),
        ("ollama", "llama3.1"),
        ("openai", "gpt-3.5-turbo"),
        # Embedding model tests
        ("bge_m3_local", None),
        ("lmstudio_embeddings", None),
        ("openai_embeddings", None),
        ("sentence_transformers", None),
    ]

    for provider, model in test_cases:
        if model:
            test_llm_provider(provider, model)
        else:
            test_embedding_provider(provider)

    print("\nTest completed!")


if __name__ == "__main__":
    main()