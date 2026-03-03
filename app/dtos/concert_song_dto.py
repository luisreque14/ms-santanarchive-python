from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class ConcertSongDto(BaseModel):
    concertId: int = Field(..., validation_alias="concert_id", serialization_alias="concertId")
    songNumber: int = Field(..., validation_alias="song_number", serialization_alias="songNumber")
    songName: str = Field(..., validation_alias="song_name", serialization_alias="songName")

    track_ids: List[int] = Field(default_factory=list, validation_alias="track_ids", serialization_alias="trackIds")
    guestArtists: List[str] = Field(default_factory=list, validation_alias="guest_artists", serialization_alias="guest_artists")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)