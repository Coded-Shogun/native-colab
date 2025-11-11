"""
Application Configuration
Loads environment variables and provides centralized configuration
"""

from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "Native Colab"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"
    API_V1_PREFIX: str = "/api/v1"

    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Security
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Password Requirements
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 300

    # Email / SMTP
    SMTP_ENABLED: bool = True
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    MAIL_FROM: str = "noreply@nativecolab.com"
    MAIL_FROM_NAME: str = "Native Colab"

    # File Storage (MinIO/S3)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin123"
    S3_BUCKET: str = "nativecolab"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False

    # Upload Limits
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB
    ALLOWED_FILE_TYPES: str = "pdf,doc,docx,xls,xlsx,ppt,pptx,txt,csv,jpg,jpeg,png,gif,mp4,mov,avi"

    @property
    def allowed_file_types_list(self) -> List[str]:
        """Convert ALLOWED_FILE_TYPES string to list"""
        return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(",")]

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Socket.io
    SOCKETIO_MESSAGE_QUEUE: str = "redis://localhost:6379/2"
    SOCKETIO_CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"

    @property
    def socketio_cors_origins_list(self) -> List[str]:
        """Convert SOCKETIO_CORS_ALLOWED_ORIGINS string to list"""
        return [origin.strip() for origin in self.SOCKETIO_CORS_ALLOWED_ORIGINS.split(",")]

    # WebRTC
    STUN_SERVER: str = "stun:stun.l.google.com:19302"
    TURN_SERVER: Optional[str] = None
    TURN_USERNAME: Optional[str] = None
    TURN_PASSWORD: Optional[str] = None

    # Push Notifications
    FCM_SERVER_KEY: Optional[str] = None
    VAPID_PUBLIC_KEY: Optional[str] = None
    VAPID_PRIVATE_KEY: Optional[str] = None

    # OAuth2
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None

    # Webhooks
    WEBHOOKS_ENABLED: bool = True
    WEBHOOKS_MAX_RETRIES: int = 3
    WEBHOOKS_TIMEOUT: int = 30

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    PROMETHEUS_ENABLED: bool = True

    # Feature Flags
    FEATURE_CHAT: bool = True
    FEATURE_PROJECTS: bool = True
    FEATURE_DOCUMENTS: bool = True
    FEATURE_SIGNATURES: bool = True
    FEATURE_TIME_TRACKING: bool = True
    FEATURE_WHITEBOARD: bool = True
    FEATURE_VIDEO_CALLS: bool = True
    FEATURE_EMAIL: bool = True
    FEATURE_CALENDAR: bool = True

    # Search
    SEARCH_ENGINE: str = "postgres"  # postgres or elasticsearch
    ELASTICSEARCH_URL: Optional[str] = None

    # Session
    SESSION_COOKIE_NAME: str = "nativecolab_session"
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"

    # Workspace Defaults
    DEFAULT_WORKSPACE_NAME: str = "My Workspace"
    MAX_WORKSPACES_PER_USER: int = 5
    MAX_USERS_PER_WORKSPACE: int = 1000

    # Timezone & Localization
    DEFAULT_TIMEZONE: str = "UTC"
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: str = "en,es,fr,de"


# Create global settings instance
settings = Settings()
