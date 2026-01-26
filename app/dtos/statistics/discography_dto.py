from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class InstrumentalStatsDto(BaseModel):
    albumId: Optional[int] = Field(None, validation_alias="album_id", serialization_alias="albumId")
    albumTitle: str = Field(..., validation_alias="album_name", serialization_alias="albumTitle")
    totalInstrumental: int = Field(..., validation_alias="total_instrumental", serialization_alias="totalInstrumental")
    totalVocal: int = Field(..., validation_alias="total_vocal", serialization_alias="totalVocal")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class ExecutiveSummaryDto(BaseModel):
    totalTracks: int = Field(..., validation_alias="total_tracks", serialization_alias="totalTracks")
    instrumentalPercentage: float = Field(..., validation_alias="instrumental_percentage", serialization_alias="instrumentalPercentage")
    loveSongsPercentage: float = Field(..., validation_alias="love_songs_percentage", serialization_alias="loveSongsPercentage")
    mostUsedKey: str = Field(..., validation_alias="most_used_key", serialization_alias="mostUsedKey")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class LoveSongStatsDto(BaseModel):
    totalTracks: int = Field(..., validation_alias="total_tracks", serialization_alias="totalTracks")
    loveSongsCount: int = Field(..., validation_alias="love_songs_count", serialization_alias="loveSongsCount")
    nonLoveSongsCount: int = Field(..., validation_alias="non_love_songs_count", serialization_alias="nonLoveSongsCount")
    loveSongsPercentage: float = Field(..., validation_alias="love_songs_percentage", serialization_alias="loveSongsPercentage")
    nonLoveSongsPercentage: float = Field(..., validation_alias="non_love_songs_percentage", serialization_alias="nonLoveSongsPercentage")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class MusicalGenreStatsDto(BaseModel):
    genreId: int = Field(..., validation_alias="genre_id", serialization_alias="genreId")
    genreName: str = Field(..., validation_alias="genre_name", serialization_alias="genreName")
    trackCount: int = Field(..., validation_alias="track_count", serialization_alias="trackCount")
    percentage: float = Field(..., validation_alias="percentage", serialization_alias="percentage")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class GuestArtistReportDto(BaseModel):
    period: str = Field(..., validation_alias="period", serialization_alias="period")
    totalTracks: int = Field(..., validation_alias="total_tracks", serialization_alias="totalTracks")
    guestArtistTracks: int = Field(..., validation_alias="guest_artist_tracks", serialization_alias="guestArtistTracks")
    guestArtistPercentage: float = Field(..., validation_alias="guest_artist_percentage", serialization_alias="guestArtistPercentage")
    guestArtists: List[str] = Field(..., validation_alias="guest_artists", serialization_alias="guestArtists")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    
class InstrumentalTrackByYearDto(BaseModel):
    year: int
    totalTracks: int