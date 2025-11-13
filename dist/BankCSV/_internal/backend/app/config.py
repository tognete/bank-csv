from functools import lru_cache
from pathlib import Path
from typing import Optional
import sys

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Basic runtime configuration.
    """

    app_name: str = "Bank CSV Extractor"
    debug: bool = Field(default=False, description="Enable verbose logging.")
    frontend_dist: Optional[Path] = Field(
        default=None, description="Optional path to built frontend assets."
    )
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:4173",
            "http://localhost:3000",
        ]
    )

    class Config:
        env_file = ".env"

    @field_validator("frontend_dist", mode="before")
    @classmethod
    def resolve_frontend_dist(cls, value: str | Path | None):
        if value:
            path = Path(value).expanduser().resolve()
            return path if path.exists() else None

        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
        default_path = base_dir / "frontend" / "dist"
        return default_path if default_path.exists() else None


@lru_cache
def get_settings() -> Settings:
    return Settings()
