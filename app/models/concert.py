from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class ConcertSchema(BaseModel):
    id: int = Field(..., description="Sequential ID")
    date: datetime = Field(..., description="Date and time of the concert (ISO 8601)")
    tour_name: Optional[str] = Field("No Tour / One-off Show", min_length=3)
    venue: str = Field(..., min_length=2)
    city_id: int = Field(..., description="Reference to the city ID")
    is_festival: bool = False
    setlist: List[str] = Field(default_factory=list, description="List of track titles performed")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
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
    )