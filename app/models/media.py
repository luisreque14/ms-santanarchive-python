from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class AlbumPhotoSchema(BaseModel):
    album_id: int = Field(..., description="Reference to the album ID")
    url: str = Field(..., min_length=10, description="Storage URL for the photo")
    description: Optional[str] = Field(None, max_length=255)
    is_cover: bool = Field(False, description="Identifies if this is the official cover art")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "album_id": 1,
                "url": "https://storage.googleapis.com/santana-archive/covers/abraxas.jpg",
                "description": "Front cover of Abraxas album",
                "is_cover": True
            }
        }
    )

class ConcertVideoSchema(BaseModel):
    concert_id: int = Field(..., description="Reference to the concert ID")
    url: str = Field(..., min_length=10)
    title: str = Field(..., min_length=3, description="Video title (e.g., Soul Sacrifice at Woodstock)")
    quality: Optional[str] = Field("HD", pattern=r"^(4K|HD|SD|720p|1080p)$")
    source: str = Field("YouTube", description="Platform or storage origin")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "concert_id": 1,
                "url": "https://www.youtube.com/watch?v=JaaT_7N_BfE",
                "title": "Soul Sacrifice Live at Woodstock",
                "quality": "HD",
                "source": "YouTube"
            }
        }
    )