from pydantic import BaseModel, Field, ConfigDict
from typing import List

class MetadataDto(BaseModel):
    # Lee 'key' -> Escribe 'musicalKey'
    musicalKey: str = Field(..., validation_alias="key", serialization_alias="musicalKey")
    isInstrumental: bool = Field(..., validation_alias="is_instrumental", serialization_alias="isInstrumental")
    isLive: bool = Field(..., validation_alias="is_live", serialization_alias="isLive")
    isLoveSong: bool = Field(..., validation_alias="is_love_song", serialization_alias="isLoveSong")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class SongFlatDto(BaseModel):
    albumId: int = Field(..., validation_alias="album_id", serialization_alias="albumId")
    albumTitle: str = Field(..., validation_alias="album_name", serialization_alias="albumTitle")
    albumCover: str = Field(..., validation_alias="album_cover", serialization_alias="albumCover")
    title: str = Field(..., validation_alias="title", serialization_alias="title")
    trackNumber: int = Field(..., validation_alias="track_number", serialization_alias="trackNumber")
    side: str = Field(..., validation_alias="side", serialization_alias="side")
    duration: str = Field(..., validation_alias="duration", serialization_alias="duration")
    composerIds: List[int] = Field(..., validation_alias="composer_ids", serialization_alias="composerIds")
    genreIds: List[int] = Field(..., validation_alias="genre_ids", serialization_alias="genreIds")
    metadata: MetadataDto = Field(..., validation_alias="metadata", serialization_alias="metadata")

    model_config = ConfigDict(
        populate_by_name=True, 
        from_attributes=True
    )