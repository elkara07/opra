"""Application configuration via Pydantic Settings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "callcenter"
    app_env: str = "development"
    debug: bool = False
    secret_key: str = "change-me-in-production-min-32-chars!!"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://callcenter:callcenter_pass@localhost:5432/callcenter"
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_secret: str = "dev-secret-change-in-production!!"
    jwt_private_key_path: str = ""
    jwt_public_key_path: str = ""
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Config encryption
    config_encryption_key: str = "change-me-32-char-encryption-key!"

    # Microsoft Graph
    ms_graph_tenant_id: str = ""
    ms_graph_client_id: str = ""
    ms_graph_client_secret: str = ""
    ms_graph_webhook_secret: str = ""

    # Jira
    jira_site_url: str = ""
    jira_api_email: str = ""
    jira_api_token: str = ""
    jira_webhook_secret: str = ""

    # LDAP
    ldap_server_url: str = ""
    ldap_bind_dn: str = ""
    ldap_bind_password: str = ""
    ldap_base_dn: str = ""
    ldap_user_search_filter: str = "(&(objectClass=user)(sAMAccountName={username}))"
    ldap_group_search_filter: str = "(&(objectClass=group)(member={user_dn}))"

    # Voice
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    deepgram_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # LiveKit
    livekit_url: str = "ws://livekit-server:7880"
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_attachments: str = "attachments"
    minio_bucket_recordings: str = "recordings"
    minio_use_ssl: bool = False

    # Internal service key
    internal_service_key: str = "internal_callcenter_2026"

    # CORS
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def jwt_private_key(self) -> str | None:
        if self.jwt_private_key_path:
            path = Path(self.jwt_private_key_path)
            if path.exists():
                return path.read_text()
        return None

    @property
    def jwt_public_key(self) -> str | None:
        if self.jwt_public_key_path:
            path = Path(self.jwt_public_key_path)
            if path.exists():
                return path.read_text()
        return None

    @property
    def effective_jwt_algorithm(self) -> str:
        if self.jwt_private_key:
            return "RS256"
        return "HS256"


settings = Settings()
