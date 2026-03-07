from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "bs1"
    api_prefix: str = "/api/v1"
    debug: bool = False

    openai_api_key: str | None = None
    openai_prompt_model: str = "gpt-5.4"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()