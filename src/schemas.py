from pydantic import BaseModel, Field


class EventInput(BaseModel):
    ip: str | None = None
    type: str = Field(default="blocked_or_suspicious", max_length=64)
    path: str | None = Field(default=None, max_length=256)
    ua: str | None = Field(default=None, max_length=256)
