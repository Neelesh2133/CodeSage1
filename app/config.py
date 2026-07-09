from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    openrouter_api_key: str
    jwt_secret: str
    github_token: str | None = None
    github_webhook_secret: str
    webhook_review_user_email: str
    

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()        