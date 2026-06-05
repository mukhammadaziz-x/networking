import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "development"
    PROJECT_NAME: str = "ClothCRM"
    SECRET_KEY: str = "supersecretkeyreplaceinproduction1234567890"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/clothcrm"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate settings
settings = Settings()
