from pydantic import BaseModel, Field
from typing import List, Optional

class PerformanceCreditSchema(BaseModel):
    concert_id: int
    musician_id: int
    instruments: List[str] = Field(..., example=["Guitarra", "Vocales"])
    is_substitute: bool = False  # Para marcar si fue un músico de reemplazo esa noche
    notes: Optional[str] = None  # Ejemplo: "Invitado especial solo en Soul Sacrifice"

    class Config:
        json_schema_extra = {
            "example": {
                "concert_id": 1,
                "musician_id": 5,
                "instruments": ["Percusión"],
                "is_substitute": False,
                "notes": "Miembro oficial de la gira"
            }
        }