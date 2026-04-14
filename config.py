"""
Insurance AI Application - Configuration Management
Centralized configuration from environment variables
"""

from dotenv import load_dotenv
import os
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application Settings"""
    
    # Application
    app_name: str = os.getenv("APP_NAME", "Insurance AI Platform")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    app_mode: str = os.getenv("APP_MODE", "development")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # API
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_title: str = os.getenv("API_TITLE", "Insurance AI API")
    api_description: str = os.getenv("API_DESCRIPTION", "AI-powered insurance processing system")
    
    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_deployment_name: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    openai_api_version: str = os.getenv("OPENAI_API_VERSION", "2024-02-15-preview")
    
    # Azure Storage
    azure_storage_account_name: Optional[str] = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    azure_storage_account_key: Optional[str] = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    azure_storage_container_name: str = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "insurance-documents")
    
    # Azure Cosmos DB
    azure_cosmos_endpoint: Optional[str] = os.getenv("AZURE_COSMOS_ENDPOINT")
    azure_cosmos_key: Optional[str] = os.getenv("AZURE_COSMOS_KEY")
    azure_cosmos_database: str = os.getenv("AZURE_COSMOS_DATABASE", "insurance-db")
    
    # Azure Document Intelligence
    azure_document_intelligence_endpoint: Optional[str] = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    azure_document_intelligence_key: Optional[str] = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/application.log")
    
    # Features
    enable_document_processing: bool = os.getenv("ENABLE_DOCUMENT_PROCESSING", "true").lower() == "true"
    enable_ai_chat: bool = os.getenv("ENABLE_AI_CHAT", "true").lower() == "true"
    enable_policy_analysis: bool = os.getenv("ENABLE_POLICY_ANALYSIS", "true").lower() == "true"
    enable_claim_processing: bool = os.getenv("ENABLE_CLAIM_PROCESSING", "true").lower() == "true"
    
    @classmethod
    def is_azure_configured(cls) -> bool:
        """Check if Azure services are configured"""
        return bool(
            cls.azure_openai_endpoint and
            cls.azure_openai_api_key and
            cls.azure_openai_deployment_name
        )
    
    @classmethod
    def is_storage_configured(cls) -> bool:
        """Check if Azure Storage is configured"""
        return bool(
            cls.azure_storage_account_name and
            cls.azure_storage_account_key
        )
    
    @classmethod
    def is_cosmos_configured(cls) -> bool:
        """Check if Azure Cosmos DB is configured"""
        return bool(
            cls.azure_cosmos_endpoint and
            cls.azure_cosmos_key
        )
    
    @classmethod
    def get_log_file_path(cls) -> str:
        """Get log file path, creating directory if needed"""
        log_dir = os.path.dirname(cls.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        return cls.log_file

# Instance
settings = Settings()
