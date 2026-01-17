from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ContinentSchema(BaseModel):
    id: int = Field(..., description="Sequential ID for the continent")
    code: str = Field(..., min_length=2, max_length=5, description="Continent code (e.g., AM, EU)")
    name: str = Field(..., min_length=3)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "code": "AM",
                "name": "Americas"
            }
        }
    )

class CountrySchema(BaseModel):
    id: int
    code: str = Field(..., min_length=2, max_length=3)
    continent_id: int
    name: str = Field(..., min_length=2)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "code": "MX",
                "continent_id": 1,
                "name": "Mexico"
            }
        }
    )

class StateSchema(BaseModel):
    id: Optional[int] = Field(None, description="Sequential ID")
    country_id: int
    code: str = Field(..., min_length=2, max_length=5)
    name: str = Field(..., min_length=2)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 10,
                "country_id": 1,
                "code": "TX",
                "name": "Texas"
            }
        }
    )

class CitySchema(BaseModel):
    id: int
    country_id: int
    state_id: Optional[int] = None
    code: str = Field(..., min_length=2, max_length=5)
    name: str = Field(..., min_length=2)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 100,
                "country_id": 1,
                "state_id": 10,
                "code": "AUST",
                "name": "Austin"
            }
        }
    )