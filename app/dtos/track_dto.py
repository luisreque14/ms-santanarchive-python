from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class ComposerDto(BaseModel):
    composerId: int = Field(..., validation_alias="id", serialization_alias="composerId")
    fullName: str = Field(..., validation_alias="full_name", serialization_alias="fullName")
    countryName: Optional[str] = Field(None, validation_alias="country_name", serialization_alias="countryName")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class TrackMetadataDto(BaseModel):
    musicalKey: str = Field(..., validation_alias="key", serialization_alias="musicalKey")
    isInstrumental: bool = Field(..., validation_alias="is_instrumental", serialization_alias="isInstrumental")
    isLive: bool = Field(..., validation_alias="is_live", serialization_alias="isLive")
    isLoveSong: bool = Field(..., validation_alias="is_love_song", serialization_alias="isLoveSong")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class TrackDto(BaseModel):
    title: str = Field(..., validation_alias="title", serialization_alias="title")
    genres: List[str] = Field(default_factory=list, validation_alias="genres", serialization_alias="genres")
    composers: List[str] = Field(default_factory=list, validation_alias="composers", serialization_alias="composers")
    metadata: TrackMetadataDto = Field(..., validation_alias="metadata", serialization_alias="metadata")
    guestArtists: List[str] = Field(default_factory=list, validation_alias="guestArtists", serialization_alias="guestArtists")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
class TrackWithAlbumDetailsDto(TrackDto):
    albumId: int = Field(..., validation_alias="albumId", serialization_alias="albumId")
    albumTitle: str = Field(..., validation_alias="albumTitle", serialization_alias="albumTitle")
    albumReleaseYear: int = Field(..., validation_alias="albumReleaseYear", serialization_alias="albumReleaseYear")
    albumCover: Optional[str] = Field(None, validation_alias="cover", serialization_alias="albumCover")
    
class GenreFilterDto(BaseModel):
    genreName: str = Field(..., validation_alias="genre_name", serialization_alias="genreName")
    tracks: List[TrackDto] = Field(..., validation_alias="tracks", serialization_alias="tracks")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)