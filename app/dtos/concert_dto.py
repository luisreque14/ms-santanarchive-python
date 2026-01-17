from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class ConcertDto(BaseModel):
    # validation_alias: Mapea desde la BD (snake_case / id)
    # serialization_alias: Mapea hacia el JSON de la API (camelCase)
    concertId: int = Field(
        ..., 
        validation_alias="id", 
        serialization_alias="concertId"
    )
    concertDate: datetime = Field(
        ..., 
        validation_alias="date", 
        serialization_alias="concertDate"
    )
    tourName: Optional[str] = Field(
        None, 
        validation_alias="tour_name", 
        serialization_alias="tourName"
    )
    venueName: str = Field(
        ..., 
        validation_alias="venue", 
        serialization_alias="venueName"
    )
    cityId: int = Field(
        ..., 
        validation_alias="city_id", 
        serialization_alias="cityId"
    )
    isFestival: bool = Field(
        False, 
        validation_alias="is_festival", 
        serialization_alias="isFestival"
    )
    setlist: List[str] = Field(
        default_factory=list, 
        validation_alias="setlist", 
        serialization_alias="setlist"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )