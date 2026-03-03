
from pydantic import BaseModel, Field, ConfigDict

class ConcertYearDto(BaseModel):
    year: int = Field(0, validation_alias="year", serialization_alias="year")
    totalConcerts: int = Field(0, validation_alias="total_concerts", serialization_alias="totalConcerts")
    totalDifferentSongs: int = Field(0, validation_alias="different_songs_count", serialization_alias="totalDifferentSongs")

    model_config = ConfigDict(populate_by_name=True)

