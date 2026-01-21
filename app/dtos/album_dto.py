from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import date

class SongDto(BaseModel):
    trackNumber: int = Field(..., validation_alias="track_number", serialization_alias="trackNumber")
    title: str = Field(..., validation_alias="title", serialization_alias="title")
    duration: str = Field(..., validation_alias="duration", serialization_alias="duration")
    composers: List[str] = Field(default_factory=list, validation_alias="composers", serialization_alias="composers")
    side: Optional[str] = Field("A", validation_alias="side", serialization_alias="side")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

class AlbumDto(BaseModel):
    id: int = Field(..., validation_alias="id", serialization_alias="id")
    title: str = Field(..., validation_alias="title", serialization_alias="title")
    releaseYear: int = Field(..., validation_alias="release_year", serialization_alias="releaseYear")
    releaseDate: date = Field(..., validation_alias="release_date")
    cover: Optional[str] = Field(None, validation_alias="cover", serialization_alias="cover")
    duration: int = Field(..., validation_alias="duration", serialization_alias="duration")
    isLive: bool = Field(..., validation_alias="is_live", serialization_alias="isLive")
    
    # Hacemos label y producer opcionales con valor None por defecto
    #label: Optional[str] = Field(None, validation_alias="label", serialization_alias="label")
    #producer: Optional[str] = Field(None, validation_alias="producer", serialization_alias="producer")
    #studio: Optional[str] = Field(None, validation_alias="studio", serialization_alias="studio")
    
    # IMPORTANTE: default_factory=list evita que falle si no hay canciones registradas
    tracklist: List[SongDto] = Field(default_factory=list, validation_alias="tracklist", serialization_alias="tracklist")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )