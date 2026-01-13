from pydantic import BaseModel, Field
from typing import List, Optional

class SongSchema(BaseModel):
    track_number: int
    title: str
    duration: str  # Formato "MM:SS"
    composers: List[str]
    side: Optional[str] = "A"  # Para los vinilos: A o B

class AlbumSchema(BaseModel):
    id: int
    title: str
    release_year: int
    label: str  # Ej: Columbia, Arista
    producer: str
    studio: Optional[str] = None
    # Aquí anidamos la lista de canciones
    tracklist: List[SongSchema]

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Abraxas",
                "release_year": 1970,
                "label": "Columbia",
                "producer": "Fred Catero, Santana",
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