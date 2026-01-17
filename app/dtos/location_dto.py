from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ContinentDto(BaseModel):
    # validation_alias: Lee de la BD ('id')
    # serialization_alias: Escribe en el JSON ('continentId')
    continentId: int = Field(..., validation_alias="id", serialization_alias="continentId")
    continentCode: str = Field(..., validation_alias="code", serialization_alias="continentCode")
    continentName: str = Field(..., validation_alias="name", serialization_alias="continentName")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class CountryDto(BaseModel):
    countryId: int = Field(..., validation_alias="id", serialization_alias="countryId")
    countryCode: str = Field(..., validation_alias="code", serialization_alias="countryCode")
    continentId: int = Field(..., validation_alias="continent_id", serialization_alias="continentId")
    countryName: str = Field(..., validation_alias="name", serialization_alias="countryName")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class StateDto(BaseModel):
    stateId: Optional[int] = Field(None, validation_alias="id", serialization_alias="stateId")
    countryId: int = Field(..., validation_alias="country_id", serialization_alias="countryId")
    stateCode: str = Field(..., validation_alias="code", serialization_alias="stateCode")
    stateName: str = Field(..., validation_alias="name", serialization_alias="stateName")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class CityDto(BaseModel):
    cityId: int = Field(..., validation_alias="id", serialization_alias="cityId")
    countryId: int = Field(..., validation_alias="country_id", serialization_alias="countryId")
    stateId: Optional[int] = Field(None, validation_alias="state_id", serialization_alias="stateId")
    cityCode: str = Field(..., validation_alias="code", serialization_alias="cityCode")
    cityName: str = Field(..., validation_alias="name", serialization_alias="cityName")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )