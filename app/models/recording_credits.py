from pydantic import BaseModel, Field
from typing import List

class RecordingCreditSchema(BaseModel):
    album_id: int
    musician_id: int
    # En grabaciones es común especificar si fue invitado o miembro oficial
    is_guest: bool = False
    instruments: List[str] = Field(..., example=["Hammond B3 Organ", "Vocals"])

    class Config:
        json_schema_extra = {
            "example": {
                "album_id": 1,
                "musician_id": 10,
                "is_guest": True,
                "instruments": ["Piano"]
            }
        }