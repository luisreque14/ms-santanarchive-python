from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class AlbumPhotoSchema(BaseModel):
    album_id: int
    url: str  # Usamos str para mayor flexibilidad con URLs de storage
    description: Optional[str] = None
    is_cover: bool = False  # Para identificar la portada oficial

class ConcertVideoSchema(BaseModel):
    concert_id: int
    url: str  # Ej: "https://www.youtube.com/watch?v=..."
    title: str # Ej: "Soul Sacrifice Live at Woodstock"
    quality: Optional[str] = "HD" # 4K, HD, SD
    source: str = "YouTube" # YouTube, Vimeo, Private Storage