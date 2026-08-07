from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_seconds: float = 60
    public_api_url: str = "https://api.piroxeno.com"
    default_client_slug: str = "piroxeno"
    require_widget_origin: bool = True
    default_rate_limit_per_minute: int = 30
    admin_api_token: str | None = None

    # Optional legacy settings used only by the old Supabase-backed routes.
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None


settings = Settings()
