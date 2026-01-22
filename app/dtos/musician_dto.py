from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import date

class RoleDto(BaseModel):
    # Lee 'id' de BD -> Escribe 'roleId' en JSON
    roleId: int = Field(..., validation_alias="id", serialization_alias="roleId")
    # Lee 'name' de BD -> Escribe 'roleName' en JSON
    roleName: str = Field(..., validation_alias="name", serialization_alias="roleName")
    category: Optional[str] = Field(None, validation_alias="category", serialization_alias="category")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class MusicianDto(BaseModel):
    musicianId: int = Field(..., validation_alias="id", serialization_alias="musicianId")
    firstName: str = Field(..., validation_alias="first_name", serialization_alias="firstName")
    lastName: str = Field(..., validation_alias="last_name", serialization_alias="lastName")
    nickname: Optional[str] = Field(None, validation_alias="nickname", serialization_alias="nickname")
    countryId: int = Field(..., validation_alias="country_id", serialization_alias="countryId")
    countryName: str = Field(..., validation_alias="country_name", serialization_alias="countryName")
    activeFrom: date = Field(..., validation_alias="active_from", serialization_alias="activeFrom")
    activeTo: Optional[date] = Field(None, validation_alias="active_to", serialization_alias="activeTo")
    roles: List[int] = Field(default_factory=list, validation_alias="roles", serialization_alias="roles")
    biography: Optional[str] = Field(None, validation_alias="bio", serialization_alias="biography")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class BandDto(BaseModel):
    # Al ser listas de DTOs, la serialización por alias se propaga automáticamente
    roles: List[RoleDto] = Field(..., validation_alias="roles", serialization_alias="roles")
    musicians: List[MusicianDto] = Field(..., validation_alias="musicians", serialization_alias="musicians")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    
class MusicianDetailsDto(MusicianDto):
    numberOfTracks: Optional[int] = Field(..., validation_alias="number_of_tracks", serialization_alias="numberOfTracks")
