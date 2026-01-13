from typing import Optional

from pydantic import BaseModel

class InstrumentalStatsResponse(BaseModel):
    album_id: Optional[int] = None
    album_name: str
    total_instrumental: int
    total_vocal: int