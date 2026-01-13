from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ConcertSchema(BaseModel):
    id: int = Field(..., description="Sequential ID")
    date: datetime  # Incluye fecha y hora si se conoce
    tour_name: Optional[str] = "No Tour / One-off Show"
    venue: str  # Ej: "Woodstock", "Madison Square Garden"
    city_id: int
    is_festival: bool = False
    setlist: List[str] = [] # Lista de títulos de canciones tocadas

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "date": "1969-08-16T14:00:00",
                "tour_name": "Santana 1969 Tour",
                "venue": "Woodstock Music & Art Fair",
                "city_id": 105,
                "is_festival": True,
                "setlist": ["Waiting", "Evil Ways", "Soul Sacrifice"]
            }
        }