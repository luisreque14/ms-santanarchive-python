from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ConcertDto(BaseModel):
    concertDate: datetime = Field(..., validation_alias="concert_date", serialization_alias="concertDate")
    venueName: str = Field(..., validation_alias="venue_name", serialization_alias="venueName")
    
    venueTypeId: int = Field(..., validation_alias="venue_type_id", serialization_alias="venueTypeId")
    venueTypeName: str = Field(..., validation_alias="venue_type_name", serialization_alias="venueTypeName")
    
    showTypeId: int = Field(..., validation_alias="show_type_id", serialization_alias="showTypeId")
    showTypeName: str = Field(..., validation_alias="show_type_name", serialization_alias="showTypeName")
    showTime: Optional[str] = Field(None, validation_alias="show_time", serialization_alias="showTime")
    
    concertTypeId: int = Field(..., validation_alias="concert_type_id", serialization_alias="concertTypeId")
    concertTypeName: str = Field(..., validation_alias="concert_type_name", serialization_alias="concertTypeName")
    
    tourId: Optional[int] = Field(None, validation_alias="tour_id", serialization_alias="tourId")
    tourName: Optional[str] = Field(None, validation_alias="tour_name", serialization_alias="tourName")
    
    cityId: int = Field(..., validation_alias="city_id", serialization_alias="cityId")
    cityName: str = Field(..., validation_alias="city_name", serialization_alias="cityName")
    
    stateId: Optional[int] = Field(None, validation_alias="state_id", serialization_alias="stateId")
    stateName: Optional[str] = Field(None, validation_alias="state_name", serialization_alias="stateName")
    
    countryId: int = Field(..., validation_alias="country_id", serialization_alias="countryId")
    countryName: str = Field(..., validation_alias="country_name", serialization_alias="countryName")
    
    continentId: int = Field(..., validation_alias="continent_id", serialization_alias="continentId")
    continentName: str = Field(..., validation_alias="continent_name", serialization_alias="continentName")
    
    concertYear: int = Field(..., validation_alias="concert_year", serialization_alias="concertYear")
    songCount: int = Field(..., validation_alias="song_count", serialization_alias="songCount")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)