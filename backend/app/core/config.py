from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), extra="ignore")

    env: str = "local"

    database_url: str
    database_ssl_mode: str = "disable"
    redis_url: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    cors_origins: str = "http://localhost:3000"

    token_encryption_key: str
    google_client_id: str = ""
    google_client_secret: str = ""
    microsoft_client_id: str = ""
    microsoft_client_secret: str = ""
    oauth_redirect_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:3000"

    minio_endpoint_url: str = "http://localhost:9000"
    minio_public_endpoint_url: str | None = None
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket_name: str = "neurodesk-files"

    llm_provider: str = "mock"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_analysis_model: str = "gpt-4o-mini"
    llm_chat_model: str = "gpt-4o-mini"
    llm_embedding_model: str = "text-embedding-3-small"
    llm_stt_model: str = "whisper-1"
    llm_tts_model: str = "tts-1"
    llm_tts_voice: str = "alloy"
    llm_timeout_seconds: float = 30.0

    email_provider: str = "mock"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_address: str = ""
    smtp_use_tls: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def async_database_url(self) -> str:
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url

    @property
    def database_connect_args(self) -> dict:
        mode = self.database_ssl_mode.strip().lower()
        if mode in {"disable", "false", "0", "off", "no"}:
            return {"ssl": False}
        if mode in {"require", "true", "1", "on", "yes"}:
            return {"ssl": True}
        return {}


settings = Settings()
