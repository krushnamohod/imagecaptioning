"""Caption API response schema."""

from pydantic import BaseModel


class CaptionResponse(BaseModel):
    caption: str
