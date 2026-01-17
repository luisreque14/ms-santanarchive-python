from pydantic import BaseModel, Field, ConfigDict

class ExecutiveSummaryDto(BaseModel):
    # validation_alias: Cómo lo lee de la BD (snake_case)
    # serialization_alias: Cómo lo entrega FastAPI (camelCase)
    
    totalTracks: int = Field(
        ..., 
        validation_alias="total_tracks", 
        serialization_alias="totalTracks"
    )
    
    instrumentalPercentage: float = Field(
        ..., 
        validation_alias="instrumental_percentage", 
        serialization_alias="instrumentalPercentage"
    )
    
    loveSongsPercentage: float = Field(
        ..., 
        validation_alias="love_songs_percentage", 
        serialization_alias="loveSongsPercentage"
    )
    
    mostUsedKey: str = Field(
        ..., 
        validation_alias="most_used_key", 
        serialization_alias="mostUsedKey"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )