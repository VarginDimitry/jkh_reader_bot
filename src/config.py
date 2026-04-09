from enum import Enum

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class OrcModels(str, Enum):
    MINI = "PaddlePaddle/PaddleOCR-VL-1.5"
    BIG = "zai-org/GLM-OCR"


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    gemini_api_key: str

    allowed_telegram_user_ids: frozenset[int] = Field(default_factory=frozenset)

    @field_validator("allowed_telegram_user_ids", mode="before")
    def _parse_allowed_telegram_user_ids(cls, value: object) -> frozenset[int]:
        if value is None or value == "":
            return frozenset()
        if isinstance(value, frozenset):
            return value
        if isinstance(value, (set, list, tuple)):
            return frozenset(int(x) for x in value)
        if isinstance(value, str):
            parts = [p.strip() for p in value.split(",") if p.strip()]
            return frozenset(int(p) for p in parts)
        msg = f"expected comma-separated ids or iterable of int, got {type(value).__name__}"
        raise TypeError(msg)

    # lm_server_api_host: str | None = None
    # hf_token: str | None = None
    # hf_hub_cache: str | None = None
    # orc_model: OrcModels = OrcModels.MINI
