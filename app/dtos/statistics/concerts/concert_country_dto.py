
from pydantic import BaseModel, Field, ConfigDict

class ConcertCountryDto(BaseModel):
    countryName: str = Field(..., validation_alias="country_name", serialization_alias="countryName")
    totalConcerts: int = Field(0, validation_alias="concert_count", serialization_alias="totalConcerts")

    model_config = ConfigDict(populate_by_name=True)

