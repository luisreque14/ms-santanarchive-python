from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class ComposerResponse(BaseModel):
    id: int
    full_name: str
    country_name: Optional[str] = Field(None, description="Denormalized country name")

    model_config = ConfigDict(from_attributes=True)

class TrackMetadata(BaseModel):
    key: str = Field(..., description="Musical key, e.g., Am, G#")
    is_instrumental: bool
    is_live: bool
    is_love_song: bool

    model_config = ConfigDict(from_attributes=True)

class TrackResponse(BaseModel):
    title: str
    album: str = Field(..., description="Album title")
    year: int
    genres: List[str] = Field(default_factory=list)
    composers: List[str] = Field(default_factory=list)
    metadata: TrackMetadata
    guestArtists: List[str] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "title": "Black Magic Woman",
                "album": "Abraxas",
                "year": 1970,
                "genres": ["Blues Rock", "Latin Rock"],
                "composers": ["Peter Green"],
                "metadata": {
                    "key": "D",
                    "is_instrumental": False,
                    "is_live": False,
                    "is_love_song": True
                },
                "guestArtists": []
            }
        }
    )

class GenreFilterResponse(BaseModel):
    genre_name: str
    tracks: List[TrackResponse]

    model_config = ConfigDict(from_attributes=True)