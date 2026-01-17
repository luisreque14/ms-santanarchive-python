from pydantic import BaseModel
from typing import List, Optional

class ComposerResponse(BaseModel):
    id: int
    full_name: str
    country_name: Optional[str] = None

class TrackMetadata(BaseModel):
    key: str
    is_instrumental: bool
    is_live: bool
    is_love_song: bool

class TrackResponse(BaseModel):
    title: str
    album: str
    year: int
    genres: List[str]
    composers: List[str]
    metadata: TrackMetadata
    collaborators: List[str]
    
class GenreFilterResponse(BaseModel):
    genre_name: str
    tracks: List[TrackResponse]