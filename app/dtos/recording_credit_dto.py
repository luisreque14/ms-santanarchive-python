from pydantic import BaseModel, Field, ConfigDict
from typing import List

class RecordingCreditDto(BaseModel):
    # validation_alias: Cómo se lee en la BD (snake_case)
    # serialization_alias: Cómo se envía al cliente (camelCase)
    albumId: int = Field(
        ..., 
        validation_alias="album_id", 
        serialization_alias="albumId"
    )
    musicianId: int = Field(
        ..., 
        validation_alias="musician_id", 
        serialization_alias="musicianId"
    )
    isGuest: bool = Field(
        False, 
        validation_alias="is_guest", 
        serialization_alias="isGuest"
    )
    instruments: List[str] = Field(
        ..., 
        validation_alias="instruments", 
        serialization_alias="instruments"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )