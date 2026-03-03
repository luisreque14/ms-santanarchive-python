from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Any

class ConcertExecutiveSummaryDto(BaseModel):
    totalConcerts: int = Field(0, validation_alias="total_concerts", serialization_alias="totalConcerts")
    mostPlayedSong: str = Field(..., validation_alias="most_played_song", serialization_alias="mostPlayedSong")
    mostPlayedAlbum: str = Field(..., validation_alias="most_played_album", serialization_alias="mostPlayedAlbum")
    topConcertYear: int = Field(0, validation_alias="top_concert_year", serialization_alias="topConcertYear")
    topConcertCountry: str = Field(..., validation_alias="top_country", serialization_alias="topConcertCountry")
    songOpener: str = Field(..., validation_alias="song_opener", serialization_alias="songOpener")
    totalNonAlbumSongs: int = Field(0, validation_alias="total_non_album_songs", serialization_alias="totalNonAlbumSongs")

    model_config = ConfigDict(populate_by_name=True)

