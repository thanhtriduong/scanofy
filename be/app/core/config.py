from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BE_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Scanofy"
    app_env: str = "development"
    database_url: str = "sqlite:///./scanofy_dev.db"
    redis_url: str = "redis://localhost:6379"
    upload_dir: Path = Path("storage/uploads")
    max_upload_size_mb: int = 50

    object_storage_endpoint: str | None = None
    object_storage_access_key: str | None = None
    object_storage_secret_key: str | None = None
    object_storage_bucket: str | None = None

    mineru_enabled: bool = True
    mineru_command: str = "mineru-kit"
    mineru_output_dir: Path = Path("storage/mineru_outputs")
    mineru_ocr_mode: str = "auto"
    mineru_timeout_seconds: int = 900
    chandra_enabled: bool = True
    vintern_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=BE_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @staticmethod
    def _resolve_workspace_path(path: Path) -> Path:
        return path.resolve() if path.is_absolute() else (BE_ROOT / path).resolve()

    @property
    def upload_root(self) -> Path:
        return self._resolve_workspace_path(self.upload_dir)

    @property
    def mineru_output_root(self) -> Path:
        return self._resolve_workspace_path(self.mineru_output_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
