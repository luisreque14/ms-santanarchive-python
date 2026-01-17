from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class TrackMetadata(BaseModel):
    key: str = Field(..., description="Musical key (e.g., Am, G#)")
    is_instrumental: bool
    is_live: bool
    is_love_song: bool

    model_config = ConfigDict(from_attributes=True)

class TrackResponse(BaseModel):
    title: str = Field(..., min_length=1)
    album: Optional[str] = Field(None, description="Album title")
    year: Optional[int] = Field(None, ge=1900)
    genres: List[str] = Field(default_factory=list)
    composers: List[str] = Field(default_factory=list)
    metadata: TrackMetadata

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True  # Reemplaza la antigua clase Config
    )