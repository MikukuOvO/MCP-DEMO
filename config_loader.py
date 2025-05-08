"""Utility module for loading configurations from YAML files."""
import os
import yaml
from typing import Dict, Any


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file.
    
    Args:
        file_path: Path to the YAML configuration file
        
    Returns:
        Dictionary containing the configuration
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the YAML file is invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def load_azure_config() -> Dict[str, str]:
    """Load Azure OpenAI configuration from secret.yaml.
    
    Returns:
        Dictionary with Azure OpenAI configuration
    """
    try:
        config = load_yaml_config('secret.yaml')
        azure_config = config.get('azure_openai', {})
        
        # Convert to environment variable format
        return {
            'OPENAI_API_TYPE': azure_config.get('api_type'),
            'OPENAI_API_KEY': azure_config.get('api_key'),
            'OPENAI_API_BASE': azure_config.get('api_base'),
            'OPENAI_API_VERSION': azure_config.get('api_version'),
            'AZURE_OPENAI_DEPLOYMENT_NAME': azure_config.get('deployment_name'),
        }
    except Exception as e:
        print(f"Error loading Azure config: {e}")
        return {} 