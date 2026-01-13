from pydantic import BaseModel
from typing import List, Optional

class MetadataSchema(BaseModel):
    key: str
    is_instrumental: bool
    is_live: bool
    is_love_song: bool

class SongFlatResponse(BaseModel):
    album_id: int
    album_name: Optional[str] = "Unknown Album"  # Valor por defecto si falla el join
    album_cover: Optional[str] = "default_cover.jpg"
    title: str
    track_number: int
    side: str
    duration: str
    composer_ids: List[int]
    genre_ids: List[int]
    metadata: MetadataSchema