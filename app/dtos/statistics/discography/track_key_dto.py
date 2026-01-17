from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class TrackKeyStatsDto(BaseModel):
    # validation_alias: Lee del resultado de agregación/BD
    # serialization_alias: Escribe en el JSON final (camelCase)
    
    albumId: Optional[int] = Field(
        None, 
        validation_alias="album_id", 
        serialization_alias="albumId"
    )
    
    albumTitle: str = Field(
        ..., 
        validation_alias="album_name", 
        serialization_alias="albumTitle"
    )
    
    musicalKey: str = Field(
        ..., 
        validation_alias="key", 
        serialization_alias="musicalKey"
    )
    
    totalTracks: int = Field(
        ..., 
        validation_alias="count", 
        serialization_alias="totalTracks"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )