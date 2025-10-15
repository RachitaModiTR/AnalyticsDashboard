import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Datadog configuration
    DD_API_KEY = os.getenv('DD_API_KEY', 'dd_api_key_placeholder_12345678901234567890')
    DD_APPLICATION_KEY = os.getenv('DD_APPLICATION_KEY', 'dd_app_key_placeholder_abcdef1234567890abcdef1234567890abcdef12')
    DD_SITE = os.getenv('DD_SITE', 'datadoghq.com')
    
    # GitHub configuration
    # Option 1: Set directly in code (replace with your actual values)
    GITHUB_TOKEN = 'ghp_placeholder_token_1234567890abcdefghijklmnop'  # GitHub personal access token
    GITHUB_OWNER = 'your-github-org'    # GitHub organization name
    GITHUB_REPO = 'your-repository-name'     # Repository name for analytics
    
    # Option 2: Use environment variables (comment out the above and uncomment below)
    # GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    # GITHUB_OWNER = os.getenv('GITHUB_OWNER', '')
    # GITHUB_REPO = os.getenv('GITHUB_REPO', '')
    
    # Option 3: Import from separate config file (uncomment below and create github_config.py)
    # try:
    #     from github_config import GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO
    # except ImportError:
    #     GITHUB_TOKEN = None
    #     GITHUB_OWNER = ''
    #     GITHUB_REPO = ''
    
    # Azure DevOps configuration
    # Option 1: Set directly in code (replace with your actual values)
    AZURE_DEVOPS_PAT = 'ado_pat_placeholder_1234567890abcdefghijklmnopqrstuvwxyz1234567890abcdef'  # Azure DevOps PAT
    AZURE_DEVOPS_ORG = 'your-ado-org'       # Your organization name
    AZURE_DEVOPS_PROJECT = 'YourProject'        # Your project name
    AZURE_DEVOPS_AREA_PATH = ''      # Will be set via user input (optional)
    
    # Option 2: Use environment variables (comment out the above and uncomment below)
    # AZURE_DEVOPS_PAT = os.getenv('AZURE_DEVOPS_PAT')
    # AZURE_DEVOPS_ORG = os.getenv('AZURE_DEVOPS_ORG', '')
    # AZURE_DEVOPS_PROJECT = os.getenv('AZURE_DEVOPS_PROJECT', '')
    
    # Figma configuration
    # Option 1: Set directly in code (replace with your actual values)
    FIGMA_TOKEN = 'figma_token_placeholder_abcd1234567890'  # Replace with your Figma personal access token
    FIGMA_TEAM_ID = 'figma_team_id_placeholder_9876543210'    # Replace with your Figma team ID
    
    # Option 2: Use environment variables (comment out the above and uncomment below)
    # FIGMA_TOKEN = os.getenv('FIGMA_TOKEN')
    # FIGMA_TEAM_ID = os.getenv('FIGMA_TEAM_ID', '')
    
    # Application settings
    REFRESH_INTERVAL = 300  # 5 minutes in seconds
    MAX_METRICS_PER_REQUEST = 10
    DEFAULT_TIME_RANGE_HOURS = 24
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        # Note: GitHub, Azure DevOps, and Figma configurations are optional, only Datadog is required
        required_vars = ['DD_API_KEY', 'DD_APPLICATION_KEY']
        missing_vars = [var for var in required_vars if not getattr(cls, var) or getattr(cls, var) == f'your_{var.lower().replace("dd_", "").replace("_", "_")}_here']
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
