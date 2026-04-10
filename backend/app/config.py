from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "AI Engineering Drawing Evaluation System"
    api_prefix: str = "/api"
    database_url: str = f"sqlite:///{(BASE_DIR / 'backend' / 'app.db').as_posix()}"
    storage_dir: Path = BASE_DIR / "storage"
    cors_origins: list[str] = ["http://localhost:5173"]
    jwt_secret: str = "change-me-in-production"
    access_token_expire_minutes: int = 480

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

