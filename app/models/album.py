from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class SongSchema(BaseModel):
    track_number: int = Field(..., gt=0)
    title: str = Field(..., min_length=1)
    duration: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Format MM:SS")
    composers: List[str]
    side: Optional[str] = Field("A", pattern=r"^[AB]$")

    model_config = ConfigDict(from_attributes=True)

class AlbumSchema(BaseModel):
    id: int = Field(..., description="Unique album identifier")
    title: str = Field(..., min_length=1)
    release_year: int = Field(..., ge=1900, le=2100)
    label: str
    producer: str
    cover: str
    studio: Optional[str] = None
    tracklist: List[SongSchema]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Abraxas",
                "release_year": 1970,
                "label": "Columbia",
                "producer": "Fred Catero, Santana",
                "cover": "image.jpg",
                "studio": "Wally Heider Recording",
                "tracklist": [
                    {
                        "track_number": 1,
                        "title": "Singing Winds, Crying Beasts",
                        "duration": "04:48",
                        "composers": ["Michael Carabello"],
                        "side": "A"
                    },
                    {
                        "track_number": 2,
                        "title": "Black Magic Woman / Gypsy Queen",
                        "duration": "05:24",
                        "composers": ["Peter Green", "Gábor Szabó"],
                        "side": "A"
                    }
                ]
            }
        }
    )