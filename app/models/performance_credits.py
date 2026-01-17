from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class PerformanceCreditSchema(BaseModel):
    concert_id: int = Field(..., description="Reference to the concert ID")
    musician_id: int = Field(..., description="Reference to the musician ID")
    instruments: List[str] = Field(
        ..., 
        min_length=1, 
        description="List of instruments played during this performance"
    )
    is_substitute: bool = Field(False, description="Flag for replacement musicians")
    notes: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "concert_id": 1,
                "musician_id": 5,
                "instruments": ["Percusión"],
                "is_substitute": False,
                "notes": "Miembro oficial de la gira"
            }
        }
    )