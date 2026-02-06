# Model Router Example - Microsoft Foundry

This repository demonstrates how to use the Model Router in Microsoft Foundry. The Model Router is an intelligent routing layer that automatically selects the best foundational language model for your prompt based on factors like complexity, cost, and latency.

## 🚀 Features

The example script demonstrates:

- **Connecting to Model Router**: How to configure and initialize the Model Router client
- **Prompt Information**: Display the messages and prompts being sent
- **Completion Details**: Show the AI-generated response
- **Selected Model**: Information about which model was chosen by the router
- **Token Usage**: Detailed token consumption metrics (prompt, completion, and total tokens)

## 📋 Prerequisites

- Python 3.8 or higher
- An Azure AI Foundry account with Model Router deployed
- Azure AI Foundry endpoint URL and API key

## 🔧 Installation

1. Clone this repository:
```bash
git clone https://github.com/mddiallo/model-router-example.git
cd model-router-example
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual Azure credentials
# You need:
# - AZURE_INFERENCE_ENDPOINT: Your Azure AI Foundry endpoint URL
# - AZURE_INFERENCE_CREDENTIAL: Your API key
```

Alternatively, export the environment variables directly:
```bash
export AZURE_INFERENCE_ENDPOINT='https://your-resource.inference.ai.azure.com'
export AZURE_INFERENCE_CREDENTIAL='your-api-key-here'
```

## 🎯 Usage

### Primary Example (Azure AI Inference SDK)

Run the main example script:

```bash
python model_router_example.py
```

This example uses the `azure-ai-inference` SDK and demonstrates the most comprehensive features including detailed prompt, completion, model selection, and token usage information.

### Alternative Example (OpenAI-Compatible Interface)

If you prefer using the OpenAI-compatible interface:

```bash
# Set different environment variables for this example
export AZURE_OPENAI_ENDPOINT='https://your-resource.openai.azure.com'
export AZURE_OPENAI_API_KEY='your-api-key-here'
export AZURE_OPENAI_DEPLOYMENT='model-router'

# Run the alternative example
python model_router_openai_example.py
```

This example uses the `openai` SDK with Azure OpenAI compatibility.

### Expected Output

The script will display detailed information about:

1. **Configuration**: Endpoint and API key setup confirmation
2. **Prompt Information**: The messages being sent to the model
3. **Request Status**: Confirmation that the request is being processed
4. **Completion**: The AI-generated response
5. **Model Information**: Details about the selected model
6. **Token Usage**: Breakdown of tokens used (prompt, completion, total)
7. **Summary**: Key takeaways about Model Router functionality

### Example Output Structure

```
======================================================================
  MODEL ROUTER EXAMPLE - MICROSOFT FOUNDRY
======================================================================

✓ Endpoint configured: https://...
✓ API key configured: **********
✓ Model Router client initialized successfully

======================================================================
  PROMPT INFORMATION
======================================================================
Number of messages: 2

Messages:
  Message 1:
    Role: system
    Content: You are a helpful AI assistant...

  Message 2:
    Role: user
    Content: Explain what Model Router is...

======================================================================
  COMPLETION INFORMATION
======================================================================
Finish Reason: stop

Completion Text:
  [AI-generated response here]

======================================================================
  SELECTED MODEL INFORMATION
======================================================================
Selected Model: [model-name]
Response ID: [response-id]

======================================================================
  TOKEN USAGE INFORMATION
======================================================================
Prompt Tokens: 45
Completion Tokens: 128
Total Tokens: 173
```

## 📚 What is Model Router?

The Model Router in Microsoft Foundry is a smart routing service that:

- **Analyzes prompts** in real-time to understand complexity and requirements
- **Selects optimal models** from available foundational LLMs (GPT-4, GPT-3.5, etc.)
- **Balances trade-offs** between quality, cost, and latency
- **Provides single endpoint** for accessing multiple models transparently
- **Auto-updates** to leverage new model versions and capabilities

### Routing Modes

The Model Router supports different routing strategies:
- **Balanced** (default): Optimizes for overall quality and cost
- **Cost**: Prioritizes lower-cost models
- **Quality**: Prioritizes highest-quality models

## 🔍 Code Structure

The example script includes:

- `display_prompt_info()`: Shows prompt details before sending
- `display_completion_info()`: Displays the AI response
- `display_model_info()`: Shows which model was selected
- `display_token_usage()`: Breaks down token consumption
- `run_model_router_example()`: Main orchestration function

## 🛠️ Troubleshooting

### Missing Environment Variables
```
⚠️  ERROR: Missing required environment variables!
```
**Solution**: Ensure `AZURE_INFERENCE_ENDPOINT` and `AZURE_INFERENCE_CREDENTIAL` are set.

### Authentication Errors
```
⚠️  ERROR: Failed to initialize client
```
**Solution**: 
- Verify your API key is correct
- Check that your endpoint URL is properly formatted
- Ensure your Azure resource has Model Router deployed

### Connection Errors
```
⚠️  ERROR: Request failed
```
**Solution**:
- Check your network connectivity
- Verify firewall settings allow Azure connections
- Ensure the endpoint URL is accessible

## 📖 Additional Resources

- [Microsoft Foundry Model Router Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/model-router)
- [Azure AI Inference SDK](https://learn.microsoft.com/en-us/python/api/overview/azure/ai-inference-readme)
- [Model Router Concepts](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/concepts/model-router)

## 📄 License

This project is provided as an example for educational purposes.

## 🤝 Contributing

Feel free to open issues or submit pull requests to improve this example.
