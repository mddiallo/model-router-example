#!/usr/bin/env python3
"""
Model Router Example for Microsoft Foundry

This script demonstrates how to use the Model Router in Microsoft Foundry.
It shows:
- How to configure and connect to the Model Router
- The prompt sent to the model
- The completion received from the model
- Information about the selected model
- Token usage statistics
"""

import os
import sys
from typing import Dict, Any
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential


def print_section(title: str, content: str = "") -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")
    if content:
        print(content)


def display_prompt_info(messages: list) -> None:
    """Display information about the prompt being sent."""
    print_section("PROMPT INFORMATION")
    print(f"Number of messages: {len(messages)}")
    print("\nMessages:")
    for i, message in enumerate(messages, 1):
        role = message.get("role", "unknown")
        content = message.get("content", "")
        print(f"\n  Message {i}:")
        print(f"    Role: {role}")
        print(f"    Content: {content}")


def display_completion_info(response: Any) -> None:
    """Display information about the completion received."""
    print_section("COMPLETION INFORMATION")
    
    # Extract the completion text
    if response.choices and len(response.choices) > 0:
        choice = response.choices[0]
        print(f"Finish Reason: {choice.finish_reason}")
        print(f"\nCompletion Text:")
        print(f"  {choice.message.content}")
    else:
        print("No completion received")


def display_model_info(response: Any) -> None:
    """Display information about the selected model."""
    print_section("SELECTED MODEL INFORMATION")
    
    # The model field shows which model was selected by the router
    if hasattr(response, 'model') and response.model:
        print(f"Selected Model: {response.model}")
    else:
        print("Model information: Not directly available in response")
        print("Note: The Model Router selects the best model based on the prompt")
    
    # Additional model metadata
    if hasattr(response, 'system_fingerprint') and response.system_fingerprint:
        print(f"System Fingerprint: {response.system_fingerprint}")
    
    if hasattr(response, 'id') and response.id:
        print(f"Response ID: {response.id}")


def display_token_usage(response: Any) -> None:
    """Display token usage statistics."""
    print_section("TOKEN USAGE INFORMATION")
    
    if hasattr(response, 'usage') and response.usage:
        usage = response.usage
        print(f"Prompt Tokens: {usage.prompt_tokens}")
        print(f"Completion Tokens: {usage.completion_tokens}")
        print(f"Total Tokens: {usage.total_tokens}")
        
        # Calculate estimated cost (example rates - adjust based on actual pricing)
        print(f"\nToken Usage Summary:")
        print(f"  - Input: {usage.prompt_tokens} tokens")
        print(f"  - Output: {usage.completion_tokens} tokens")
        print(f"  - Total: {usage.total_tokens} tokens")
    else:
        print("Token usage information not available")


def run_model_router_example():
    """
    Main function to demonstrate Model Router usage.
    
    This function:
    1. Configures the connection to the Model Router
    2. Sends a sample prompt
    3. Displays all relevant information about the request and response
    """
    
    print_section("MODEL ROUTER EXAMPLE - MICROSOFT FOUNDRY", 
                  "Demonstrating intelligent model selection and routing")
    
    # Configuration
    # Load credentials from environment variables
    endpoint = os.getenv("AZURE_INFERENCE_ENDPOINT")
    api_key = os.getenv("AZURE_INFERENCE_CREDENTIAL")
    
    if not endpoint or not api_key:
        print("\n⚠️  ERROR: Missing required environment variables!")
        print("\nPlease set the following environment variables:")
        print("  - AZURE_INFERENCE_ENDPOINT: Your Azure AI Foundry endpoint URL")
        print("  - AZURE_INFERENCE_CREDENTIAL: Your API key")
        print("\nExample:")
        print("  export AZURE_INFERENCE_ENDPOINT='https://your-resource.azure.com'")
        print("  export AZURE_INFERENCE_CREDENTIAL='your-api-key'")
        sys.exit(1)
    
    print(f"\n✓ Endpoint configured: {endpoint}")
    print(f"✓ API key configured: {'*' * 10}****")
    
    # Initialize the client
    try:
        client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        print("✓ Model Router client initialized successfully")
    except Exception as e:
        print(f"\n⚠️  ERROR: Failed to initialize client: {e}")
        sys.exit(1)
    
    # Prepare the prompt
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant that provides clear and concise answers."
        },
        {
            "role": "user",
            "content": "Explain what Model Router is in Microsoft Foundry and why it's useful."
        }
    ]
    
    # Display prompt information
    display_prompt_info(messages)
    
    # Make the request
    print_section("MAKING REQUEST TO MODEL ROUTER")
    print("Sending request to Model Router...")
    print("The router will analyze the prompt and select the best model...")
    
    try:
        response = client.complete(
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            top_p=0.95
        )
        print("✓ Response received successfully")
        
        # Display all information about the response
        display_completion_info(response)
        display_model_info(response)
        display_token_usage(response)
        
        # Summary
        print_section("SUMMARY")
        print("✓ Successfully demonstrated Model Router usage")
        print("\nKey Points:")
        print("  • Model Router automatically selected the best model for this prompt")
        print("  • The selection considers factors like prompt complexity, cost, and latency")
        print("  • You interact with a single endpoint, abstracting model selection")
        print("  • Token usage and costs are tracked for billing and monitoring")
        
    except Exception as e:
        print(f"\n⚠️  ERROR: Request failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify your endpoint URL is correct")
        print("  2. Ensure your API key is valid and has appropriate permissions")
        print("  3. Check that the Model Router is deployed in your Azure resource")
        print("  4. Verify network connectivity to Azure")
        sys.exit(1)


def main():
    """Entry point for the script."""
    try:
        run_model_router_example()
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n⚠️  Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
