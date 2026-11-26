from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

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
    ocr_output_dir: Path = Path("storage/ocr_outputs")
    paddleocr_enabled: bool = True
    paddleocr_lang: str = "vi"
    paddleocr_timeout_seconds: int = Field(default=900, ge=1)
    paddleocr_render_dpi: int = Field(default=144, ge=72, le=300)
    paddleocr_max_pages: int = Field(default=200, ge=1)
    paddleocr_max_pixels: int = Field(default=25_000_000, ge=1)
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

    @property
    def ocr_output_root(self) -> Path:
        return self._resolve_workspace_path(self.ocr_output_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
