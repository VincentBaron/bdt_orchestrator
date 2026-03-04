from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Webhooks Global Security
    WEBHOOK_SECRET_PATH: str
    
    # Sourcing API
    SOURCING_API_URL: str
    SOURCING_API_KEY: str
    SOURCING_CLIENT_EXTERNAL_ID: str
    
    # Flatchr ATS
    FLATCHR_CAREERS_URL: str
    FLATCHR_API_URL: str
    FLATCHR_TOKEN: str
    FLATCHR_COMPANY_ID: str
    FLATCHR_API_USER_ID: int
    FLATCHR_DEFAULT_COLUMN_ID: int

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
