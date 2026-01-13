# backendf/core/env.py
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

env = "development"

# 只在開發用
if env == "development":
    dotenv_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=True)
    print(f"[DEV] dotenv loaded from: {dotenv_path}")


class Settings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str


settings = Settings()  # type: ignore
