from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class PerformanceCreditDto(BaseModel):
    # validation_alias: Cómo se llama en la BD (snake_case)
    # serialization_alias: Cómo se entrega al Frontend (camelCase)
    concertId: int = Field(
        ..., 
        validation_alias="concert_id", 
        serialization_alias="concertId"
    )
    musicianId: int = Field(
        ..., 
        validation_alias="musician_id", 
        serialization_alias="musicianId"
    )
    instruments: List[str] = Field(
        ..., 
        validation_alias="instruments", 
        serialization_alias="instruments"
    )
    isSubstitute: bool = Field(
        ..., 
        validation_alias="is_substitute", 
        serialization_alias="isSubstitute"
    )
    notes: Optional[str] = Field(
        None, 
        validation_alias="notes", 
        serialization_alias="notes"
    )

    model_config = ConfigDict(
        populate_by_name=True, 
        from_attributes=True
    )