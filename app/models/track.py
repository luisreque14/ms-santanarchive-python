from pydantic import BaseModel, Field
from typing import List, Optional

class TrackMetadata(BaseModel):
    key: str
    is_instrumental: bool
    is_live: bool
    is_love_song: bool

class TrackResponse(BaseModel):
    title: str
    album: Optional[str] = None
    year: Optional[int] = None
    genres: List[str] = []
    composers: List[str] = []
    metadata: TrackMetadata

    class Config:
        populate_by_name = True