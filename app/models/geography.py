from pydantic import BaseModel, Field
from typing import Optional # Importante para campos opcionales

class ContinentSchema(BaseModel):
    id: int = Field(..., description="Sequential ID")
    code: str = Field(..., min_length=2, max_length=5)
    name: str = Field(..., min_length=3)

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "code": "AM",
                "name": "Americas"
            }
        }

class CountrySchema(BaseModel):
    id: int
    code: str = Field(..., min_length=2, max_length=3)
    continent_id: int  # Este debe coincidir con un ID de la colección continents
    name: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "code": "MX",
                "continent_id": 1,
                "name": "Mexico"
            }
        }

class StateSchema(BaseModel):
    id: Optional[int] = Field(None, description="Sequential ID")
    country_id: int
    code: str = Field(..., min_length=2, max_length=5)
    name: str

    class Config:
        from_attributes = True  # Útil para que funcione bien con MongoDB

class CitySchema(BaseModel):
    id: int
    country_id: int
    state_id: Optional[int] = None  # Puede ser nulo si la ciudad no tiene estado
    code: str = Field(..., min_length=2, max_length=5)
    name: str
    country_id: int