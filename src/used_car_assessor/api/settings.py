from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="UCA_",
        env_file=".env",
        extra="forbid",
        case_sensitive=False,
    )

    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    model_path: Path = Path("artifacts/model.joblib")
    model_metadata_path: Path = Path("artifacts/model_metadata.json")
    redis_url: str = "redis://localhost:6379/0"
    redis_timeout_seconds: float = Field(default=1.0, gt=0, le=10)
    policy_lower_ratio: float = Field(default=0.85, gt=0, le=1)
    policy_upper_ratio: float = Field(default=1.15, ge=1, le=3)

    @model_validator(mode="after")
    def validate_policy_order(self) -> "Settings":
        if self.policy_lower_ratio > self.policy_upper_ratio:
            raise ValueError("policy lower ratio cannot exceed upper ratio")
        return self

