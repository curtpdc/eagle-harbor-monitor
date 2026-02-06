from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")
    # Database
    DATABASE_URL: str
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    
    # Azure OpenAI (optional for local dev)
    AZURE_OPENAI_ENDPOINT: str = "https://xig-openai-resource.cognitiveservices.azure.com/"
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o-mini"
    
    # Azure Communication Services Email (optional for local dev)
    AZURE_COMM_CONNECTION_STRING: Optional[str] = None
    FROM_EMAIL: str = "DoNotReply@59b6bc9f-ac74-4afa-9428-bac5c4976a23.azurecomm.net"
    
    # Application
    APP_NAME: str = "Eagle Harbor Data Center Monitor"
    APP_URL: str = "https://eagleharbormonitor.org"
    DEBUG: bool = True
    
    # Monitoring Keywords
    KEYWORDS: List[str] = [
        "data center", "datacenter", "eagle harbor", "chalk point",
        "qualified data center", "CR-98-2025", "Executive Order 42-2025",
        "Landover Mall", "zoning", "AR zone", "RE zone",
        "MNCPPC", "Planning Board", "legislative amendment"
    ]
    
    # Email Settings
    WEEKLY_DIGEST_DAY: int = 4  # Friday
    WEEKLY_DIGEST_HOUR: int = 15  # 3 PM
    
settings = Settings()
