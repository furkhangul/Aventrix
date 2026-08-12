from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_name: str = "FurOfTheWeak"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "dev-secret-change-me"
    app_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:5173"
    tracking_base_url: str = "http://localhost:8000"
    use_mock_providers: bool = True

    # Database
    database_url: str = (
        "postgresql+asyncpg://furoftheweak:change-me@localhost:5432/furoftheweak"
    )

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth / JWT
    jwt_secret_key: str = "dev-jwt-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    cookie_secure: bool = False
    cookie_domain: str | None = None

    # CORS
    cors_origins: str = "http://localhost:5173"

    # Rate limiting
    rate_limit_login_per_minute: int = 5
    rate_limit_register_per_minute: int = 3
    rate_limit_password_reset_per_minute: int = 3
    rate_limit_redirect_per_minute: int = 120
    rate_limit_api_per_minute: int = 60

    # API key tiers (spec section 21) — requests per day, keyed by ApiKeyTier
    rate_limit_api_key_free_per_day: int = 100
    rate_limit_api_key_pro_per_day: int = 10_000
    rate_limit_api_key_business_per_day: int = 100_000

    # Webhooks
    webhook_max_retry_attempts: int = 5
    webhook_delivery_timeout_seconds: int = 8

    # Background worker
    worker_sweep_interval_seconds: int = 60

    # Security Center
    security_scan_alert_threshold: int = 60

    # Seed
    seed_admin_email: str = "admin@furoftheweak.local"

    # IP intelligence
    ip_provider: str = "mock"
    ip_intelligence_api_key: str | None = None
    ip_intelligence_base_url: str | None = None
    ip_intelligence_timeout_seconds: int = 8
    ip_intelligence_fallback_provider: str = "local"

    # Reputation (adapter present, feature lands in a later phase)
    reputation_provider: str = "mock"
    reputation_api_key: str | None = None

    # Email
    email_provider: str = "mock"
    email_api_key: str | None = None
    email_from_address: str = "no-reply@furoftheweak.local"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None

    # Map
    map_provider: str = "maplibre-demo"
    map_api_key: str | None = None

    # Feature flags
    enable_qr: bool = True
    enable_webhook: bool = True
    enable_realtime: bool = False
    enable_domain_analyzer: bool = True
    enable_ai: bool = False
    enable_device_control: bool = False

    # Devices / remote control (WebRTC signaling + TURN) — see
    # docs/DEVICE_CONTROL_PROTOCOL.md. Off by default: it's the newest,
    # most privilege-sensitive module in the app.
    turn_shared_secret: str | None = None
    turn_realm: str = "furoftheweak.local"
    turn_server_url: str = "turn:localhost:3478"
    stun_server_url: str = "stun:stun.l.google.com:19302"
    device_pairing_code_ttl_seconds: int = 300
    device_session_max_duration_seconds: int = 3600
    device_ws_ticket_ttl_seconds: int = 60

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
