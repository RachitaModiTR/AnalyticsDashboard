# AI Assistant (Chatbot) Setup Guide

The Analytics Dashboard now includes an AI-powered assistant that can analyze your data and provide intelligent insights. This guide will help you configure the chatbot with your preferred LLM provider.

## Features

- **Intelligent Data Analysis**: Ask questions about your Datadog, GitHub, Azure DevOps, and Figma data
- **Multi-Provider Support**: Works with OpenAI, Anthropic Claude, or Azure OpenAI
- **Context-Aware Responses**: Analyzes real-time data from your connected services
- **Suggested Questions**: Get AI-generated question suggestions based on your data
- **Quick Actions**: Pre-built questions for common analytics needs

## LLM Provider Setup

### Option 1: OpenAI (Recommended)

1. Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Set the environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   export LLM_PROVIDER="openai"
   ```

### Option 2: Anthropic Claude

1. Get your API key from [Anthropic Console](https://console.anthropic.com/)
2. Set the environment variables:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   export LLM_PROVIDER="anthropic"
   ```

### Option 3: Azure OpenAI

1. Set up Azure OpenAI service in your Azure subscription
2. Get your endpoint, API key, and deployment name
3. Set the environment variables:
   ```bash
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   export AZURE_OPENAI_KEY="your-api-key-here"
   export AZURE_OPENAI_DEPLOYMENT="your-deployment-name"
   export LLM_PROVIDER="azure"
   ```

## Usage

1. **Access the AI Assistant**: Click on the "AI Assistant" tab in the dashboard
2. **Select Data Source**: Choose which data source to analyze (All Sources, Datadog, GitHub, Azure DevOps, or Figma)
3. **Ask Questions**: Type your question in the chat input or use the quick action buttons
4. **Get Insights**: The AI will analyze your data and provide intelligent responses

## Example Questions

- "What are the key performance trends in the last 24 hours?"
- "Show me development velocity insights from GitHub"
- "What are the main issues or bottlenecks in Azure DevOps?"
- "Give me a summary of recent activity across all platforms"
- "How is our team's productivity trending?"
- "What are the most active repositories this week?"

## Fallback Mode

If no LLM provider is configured, the chatbot will still work but provide basic fallback responses and configuration guidance.

## Troubleshooting

### Chatbot Status Shows "Not Configured"
- Check that your environment variables are set correctly
- Verify your API key is valid and has sufficient credits
- Ensure the LLM_PROVIDER variable matches your chosen provider

### API Errors
- Check your API key permissions
- Verify your Azure OpenAI deployment is active (for Azure users)
- Check rate limits and usage quotas

### No Data Available
- Ensure your data sources (Datadog, GitHub, etc.) are properly configured
- Check that you have recent data in your connected services
- Verify API permissions for data access

## Security Notes

- Never commit API keys to version control
- Use environment variables or secure configuration management
- Consider using Azure Key Vault or similar services for production deployments
- Monitor API usage and costs regularly

## Support

For issues with the AI Assistant:
1. Check the browser console for JavaScript errors
2. Verify your LLM provider configuration
3. Test with simple questions first
4. Check the application logs for backend errors
