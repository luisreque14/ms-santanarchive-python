from pydantic import BaseModel, Field, ConfigDict
from typing import List

class RecordingCreditSchema(BaseModel):
    album_id: int = Field(..., description="Reference to the album ID")
    musician_id: int = Field(..., description="Reference to the musician ID")
    # En grabaciones es común especificar si fue invitado o miembro oficial
    is_guest: bool = Field(False, description="True if the musician was a guest artist")
    instruments: List[str] = Field(
        ..., 
        min_length=1, 
        description="List of instruments played in the studio"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "album_id": 1,
                "musician_id": 10,
                "is_guest": True,
                "instruments": ["Piano"]
            }
        }
    )