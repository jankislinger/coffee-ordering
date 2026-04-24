"""Configuration management."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """LLM configuration."""

    provider: str = "openai"
    model: str = "gpt-4"
    temperature: float = 0.1
    api_key: str = Field(default="", alias="OPENAI_API_KEY")


class CacheConfig(BaseSettings):
    """Cache configuration."""

    enabled: bool = True
    ttl: int = 3600  # 1 hour in seconds


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Roaster settings
    roaster: str = "doubleshot"

    # LLM settings
    llm: LLMConfig = Field(default_factory=LLMConfig)

    # Cache settings
    cache: CacheConfig = Field(default_factory=CacheConfig)

    # DoubleShot credentials (optional)
    doubleshot_username: str = Field(default="", alias="DOUBLESHOT_USERNAME")
    doubleshot_password: str = Field(default="", alias="DOUBLESHOT_PASSWORD")

    # Dos Mundos credentials (optional)
    dosmundos_username: str = Field(default="", alias="DOSMUNDOS_USERNAME")
    dosmundos_password: str = Field(default="", alias="DOSMUNDOS_PASSWORD")


# Global settings instance
settings = Settings()
