#!/usr/bin/env python3
"""
Alternative Model Router Example using OpenAI-Compatible Interface

This script demonstrates an alternative approach to using the Model Router 
in Microsoft Foundry using the OpenAI-compatible interface through the 
azure-openai SDK.
"""

import os
import sys
from openai import AzureOpenAI


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def main():
    """Main function demonstrating OpenAI-compatible interface."""
    
    print_section("MODEL ROUTER EXAMPLE (OpenAI-Compatible Interface)")
    
    # Configuration
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "model-router")
    
    if not endpoint or not api_key:
        print("\n⚠️  ERROR: Missing required environment variables!")
        print("\nPlease set:")
        print("  - AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint URL")
        print("  - AZURE_OPENAI_API_KEY: Your API key")
        print("  - AZURE_OPENAI_DEPLOYMENT: Your deployment name (default: model-router)")
        sys.exit(1)
    
    print(f"\n✓ Endpoint: {endpoint}")
    print(f"✓ Deployment: {deployment}")
    
    # Initialize client
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-02-15-preview"
    )
    
    # Prepare messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Model Router in Azure AI?"}
    ]
    
    print_section("PROMPT INFORMATION")
    for i, msg in enumerate(messages, 1):
        print(f"Message {i}: [{msg['role']}] {msg['content']}")
    
    # Make request
    print_section("SENDING REQUEST")
    print("Requesting completion from Model Router...")
    
    response = client.chat.completions.create(
        model=deployment,
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )
    
    # Display results
    print_section("COMPLETION RECEIVED")
    print(f"Content: {response.choices[0].message.content}")
    
    print_section("MODEL INFORMATION")
    print(f"Model Used: {response.model}")
    print(f"Response ID: {response.id}")
    print(f"Finish Reason: {response.choices[0].finish_reason}")
    
    print_section("TOKEN USAGE")
    usage = response.usage
    print(f"Prompt Tokens: {usage.prompt_tokens}")
    print(f"Completion Tokens: {usage.completion_tokens}")
    print(f"Total Tokens: {usage.total_tokens}")
    
    print("\n✓ Example completed successfully!\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n⚠️  Error: {e}")
        sys.exit(1)
