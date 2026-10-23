"""Response models for caption generation history."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HistoryRecord(BaseModel):
    """A generated caption pair and its non-sensitive selection metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    base_caption: str
    generated_caption: str
    platform: str
    language: str
    writing_style: str
    visual_template: str | None = None
    created_at_utc: datetime


class HistoryListResponse(BaseModel):
    """Paginated history records, ordered newest first."""

    records: list[HistoryRecord]
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
    total: int = Field(ge=0)
