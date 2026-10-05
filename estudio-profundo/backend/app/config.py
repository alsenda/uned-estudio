"""Application settings.

Settings are read from environment variables (and a local ``.env`` file in
development). ``content_dir`` is what makes this engine generic: point it at
any folder of authored ``<slug>/document.json`` + ``<slug>/quiz.json`` files
and it works, regardless of what project the documentation came from.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = Field(default=f"sqlite:///{PROJECT_ROOT / 'backend' / 'estudio.db'}")
    content_dir: str = Field(default=str(PROJECT_ROOT / "content"))
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8000"])

    @property
    def content_path(self) -> Path:
        return Path(self.content_dir)

    def images_dir_for(self, document_id: str) -> Path:
        """Where confirmed/extracted images for one document live on disk."""
        path = self.content_path / document_id / "images"
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
