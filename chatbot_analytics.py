"""
Chatbot Analytics Module for LLM-powered data analysis and insights
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import urllib3
from config import Config
from context_storage import context_storage

# Disable SSL warnings for corporate environments
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ChatbotAnalytics:
    """Chatbot for analyzing analytics data using LLM"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.azure_openai_key = os.getenv('AZURE_OPENAI_KEY')
        self.azure_openai_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
        
        # Default to OpenAI if no specific provider is configured
        self.llm_provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        
    def _get_llm_response(self, prompt: str, context_data: Dict = None, data_source: str = "general") -> str:
        """Get response from configured LLM provider"""
        
        if self.llm_provider == 'openai':
            return self._call_openai(prompt, context_data, data_source)
        elif self.llm_provider == 'anthropic' and self.anthropic_api_key:
            return self._call_anthropic(prompt, context_data, data_source)
        elif self.llm_provider == 'azure' and self.azure_openai_endpoint:
            return self._call_azure_openai(prompt, context_data, data_source)
        else:
            return self._get_fallback_response(prompt, context_data, data_source)
    
    def _call_openai(self, prompt: str, context_data: Dict = None, data_source: str = "general") -> str:
        """Call Thomson Reuters Azure OpenAI API"""
        try:
            # Thomson Reuters API configuration
            workspace_id = "WePowerADBy"
            model_name = "gpt-4o"
            asset_id = "208321"
            
            # Get credentials from Thomson Reuters endpoint
            credentials_url = "https://aiplatform.gcs.int.thomsonreuters.com/v1/openai/token"
            credentials_payload = {"workspace_id": workspace_id, "model_name": model_name}
            
            credentials_response = requests.post(
                credentials_url, 
                json=credentials_payload,
                verify=False
            )
            
            if credentials_response.status_code != 200:
                return f"Failed to get credentials: {credentials_response.status_code} - {credentials_response.text}"
            
            credentials = credentials_response.json()
            
            if "openai_key" not in credentials or "openai_endpoint" not in credentials:
                return "Failed to retrieve OpenAI credentials from Thomson Reuters"
            
            OPENAI_API_KEY = credentials["openai_key"]
            OPENAI_DEPLOYMENT_ID = credentials["azure_deployment"]
            OPENAI_API_VERSION = credentials["openai_api_version"]
            token = credentials["token"]
            llm_profile_key = OPENAI_DEPLOYMENT_ID.split("/")[0]
            OPENAI_BASE_URL = "https://eais2-use.int.thomsonreuters.com"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "api-key": OPENAI_API_KEY,
                "Content-Type": "application/json",
                "x-tr-chat-profile-name": "ai-platforms-chatprofile-prod",
                "x-tr-userid": workspace_id,
                "x-tr-llm-profile-key": llm_profile_key,
                "x-tr-user-sensitivity": "true",
                "x-tr-sessionid": OPENAI_DEPLOYMENT_ID,
                "x-tr-asset-id": asset_id,
                "x-tr-authorization": OPENAI_BASE_URL,
            }
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a concise analytics assistant. Provide brief, actionable insights in 2-3 sentences maximum. Focus on key findings and immediate recommendations. Use HTML formatting: <strong>bold</strong>, <ul><li>bullet points</li></ul>, <br/> for line breaks. Be direct and practical. Base your analysis on the provided context data from the analytics dashboard."
                },
                {
                    "role": "user", 
                    "content": self._format_prompt_with_context(prompt, context_data, data_source)
                }
            ]
            
            payload = {
                "model": model_name,
                "messages": messages,
                "max_tokens": 300,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{OPENAI_BASE_URL}/openai/deployments/{OPENAI_DEPLOYMENT_ID}/chat/completions?api-version={OPENAI_API_VERSION}",
                headers=headers,
                json=payload,
                timeout=30,
                verify=False  # Disable SSL verification for corporate environments
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Thomson Reuters OpenAI API Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error calling OpenAI: {str(e)}"
    
    def _call_anthropic(self, prompt: str, context_data: Dict = None, data_source: str = "general") -> str:
        """Call Anthropic Claude API"""
        try:
            headers = {
                'x-api-key': self.anthropic_api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            formatted_prompt = self._format_prompt_with_context(prompt, context_data)
            
            payload = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": formatted_prompt
                    }
                ]
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                return f"Anthropic API Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error calling Anthropic: {str(e)}"
    
    def _call_azure_openai(self, prompt: str, context_data: Dict = None, data_source: str = "general") -> str:
        """Call Azure OpenAI API"""
        try:
            headers = {
                'api-key': self.azure_openai_key,
                'Content-Type': 'application/json'
            }
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert data analyst specializing in software development analytics. Provide clear, actionable insights based on the data provided."
                },
                {
                    "role": "user",
                    "content": self._format_prompt_with_context(prompt, context_data)
                }
            ]
            
            payload = {
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            url = f"{self.azure_openai_endpoint}/openai/deployments/{self.azure_openai_deployment}/chat/completions?api-version=2023-12-01-preview"
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30,
                verify=False  # Disable SSL verification for corporate environments
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Azure OpenAI API Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error calling Azure OpenAI: {str(e)}"
    
    def _get_fallback_response(self, prompt: str, context_data: Dict = None, data_source: str = "general") -> str:
        """Fallback response when no LLM is configured"""
        return f"""🤖 **Analytics Bot Response**

I can see you're asking about: "{prompt}"

**Note**: No LLM provider is currently configured. To enable AI-powered analysis, please set up one of the following:

1. **OpenAI**: Set `OPENAI_API_KEY` environment variable
2. **Anthropic Claude**: Set `ANTHROPIC_API_KEY` environment variable  
3. **Azure OpenAI**: Set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`, and `AZURE_OPENAI_DEPLOYMENT`

**Available Data Sources**:
- Datadog metrics and dashboards
- GitHub pull request analytics
- Azure DevOps work items and PRs
- Figma design analytics

Once configured, I'll be able to provide intelligent insights and analysis of your data!"""
    
    def _format_prompt_with_context(self, prompt: str, context_data: Dict = None, data_source: str = "general") -> str:
        """Format the prompt with context data from storage and provided context"""
        # Get stored context from all APIs
        stored_context = context_storage.get_context_for_llm(data_source)
        
        # Add provided context data if available
        additional_context = ""
        if context_data:
            additional_context = "\n\n**Additional Context Data:**\n"
            for key, value in context_data.items():
                if isinstance(value, (dict, list)):
                    additional_context += f"- {key}: {json.dumps(value, indent=2)}\n"
                else:
                    additional_context += f"- {key}: {value}\n"
        
        # Combine all context
        full_context = f"{stored_context}{additional_context}"
        
        return f"{full_context}\n\n**Question:** {prompt}"
    
    def analyze_datadog_metrics(self, metrics_data: Dict, user_question: str) -> str:
        """Analyze Datadog metrics data"""
        prompt = f"""Analyze the following Datadog metrics data and answer the user's question: "{user_question}"

Focus on:
- Performance trends and patterns
- Anomalies or unusual behavior
- Resource utilization insights
- Recommendations for optimization

Provide actionable insights in a clear, professional format."""
        
        return self._get_llm_response(prompt, metrics_data, "datadog")
    
    def analyze_github_analytics(self, github_data: Dict, user_question: str) -> str:
        """Analyze GitHub pull request analytics"""
        prompt = f"""Analyze the following GitHub analytics data and answer the user's question: "{user_question}"

Focus on:
- Development velocity and trends
- Code review patterns
- Team productivity metrics
- Pull request quality indicators
- Recommendations for process improvement

Provide insights about development workflow and team performance."""
        
        return self._get_llm_response(prompt, github_data, "github")
    
    def analyze_azure_devops_data(self, azure_data: Dict, user_question: str) -> str:
        """Analyze Azure DevOps work items and PRs"""
        prompt = f"""Analyze the following Azure DevOps data and answer the user's question: "{user_question}"

Focus on:
- Work item completion trends
- Development cycle insights
- Team collaboration patterns
- Project progress indicators
- Process optimization opportunities

Provide actionable recommendations for project management and development workflow."""
        
        return self._get_llm_response(prompt, azure_data, "azuredevops")
    
    def analyze_figma_data(self, figma_data: Dict, user_question: str) -> str:
        """Analyze Figma design analytics"""
        prompt = f"""Analyze the following Figma design data and answer the user's question: "{user_question}"

Focus on:
- Design collaboration patterns
- Project organization insights
- Team design workflow
- Asset management efficiency
- Design system utilization

Provide insights about design process and collaboration effectiveness."""
        
        return self._get_llm_response(prompt, figma_data, "figma")
    
    def get_general_insights(self, all_data: Dict, user_question: str) -> str:
        """Get general insights across all data sources"""
        prompt = f"""Analyze the following comprehensive analytics data from multiple sources and answer the user's question: "{user_question}"

Data sources include:
- Datadog monitoring and metrics
- GitHub development analytics  
- Azure DevOps project management
- Figma design collaboration

Provide cross-platform insights, identify correlations between different data sources, and give strategic recommendations for improving overall development and design processes."""
        
        return self._get_llm_response(prompt, all_data, "general")
    
    def get_data_summary(self, data_source: str, data: Dict) -> str:
        """Get a summary of data from a specific source"""
        prompt = f"""Provide a concise executive summary of the {data_source} data below.

Include:
- Key metrics and trends
- Notable patterns or anomalies
- Top insights
- Brief recommendations

Keep it professional and actionable for management review."""
        
        return self._get_llm_response(prompt, data)
    
    def suggest_questions(self, data_source: str, available_data: Dict) -> List[str]:
        """Suggest relevant questions based on available data"""
        prompt = f"""Based on the {data_source} data available, suggest 5 relevant questions that would provide valuable insights.

The questions should be:
- Specific to the data available
- Actionable for decision-making
- Cover different aspects (performance, trends, optimization, etc.)
- Professional and business-focused

Return only the questions, one per line."""
        
        response = self._get_llm_response(prompt, available_data)
        questions = [q.strip() for q in response.split('\n') if q.strip() and '?' in q]
        return questions[:5]  # Return top 5 questions
