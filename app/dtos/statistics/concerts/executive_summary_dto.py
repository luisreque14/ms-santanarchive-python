from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Any

class ConcertExecutiveSummaryDto(BaseModel):
    totalConcerts: int = Field(0, validation_alias="total_concerts", serialization_alias="totalConcerts")
    mostPlayedSong: str = Field(..., validation_alias="most_played_song", serialization_alias="mostPlayedSong")
    mostPlayedAlbum: str = Field(..., validation_alias="most_played_album", serialization_alias="mostPlayedAlbum")


