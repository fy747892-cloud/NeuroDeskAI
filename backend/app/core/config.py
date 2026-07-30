import ssl
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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

    diarization_provider: str = "disabled"
    diarization_model: str = "pyannote/speaker-diarization-3.1"
    hf_token: str = ""

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
        database_url = self.database_url
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        parts = urlsplit(database_url)
        if parts.scheme != "postgresql+asyncpg":
            return database_url

        unsupported_asyncpg_params = {"sslmode", "channel_binding"}
        query = urlencode(
            [
                (key, value)
                for key, value in parse_qsl(parts.query, keep_blank_values=True)
                if key not in unsupported_asyncpg_params
            ]
        )
        return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))

    @property
    def database_connect_args(self) -> dict:
        mode = self.database_ssl_mode.strip().lower()
        if mode in {"disable", "false", "0", "off", "no"}:
            return {"ssl": False}
        if mode in {"require", "true", "1", "on", "yes"}:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            return {"ssl": ssl_context}
        return {}


settings = Settings()
