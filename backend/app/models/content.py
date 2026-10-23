
from pydantic import BaseModel, Field, field_validator

from app.config import (
    SUPPORTED_LANGUAGES,
    SUPPORTED_PLATFORMS,
    SUPPORTED_STYLES,
)


class ContentGenerationRequest(BaseModel):
    image_caption: str = Field(min_length=1, max_length=2000)
    platform: str
    language: str
    style: str

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, value: str) -> str:
        if value not in SUPPORTED_PLATFORMS:
            raise ValueError(
                f"Unsupported platform. Choose from: {SUPPORTED_PLATFORMS}"
            )
        return value

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        if value not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language. Choose from: {SUPPORTED_LANGUAGES}"
            )
        return value

    @field_validator("style")
    @classmethod
    def validate_style(cls, value: str) -> str:
        if value not in SUPPORTED_STYLES:
            raise ValueError(
                f"Unsupported style. Choose from: {SUPPORTED_STYLES}"
            )
        return value


class ContentGenerationResponse(BaseModel):
    caption: str
