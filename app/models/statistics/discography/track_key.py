from pydantic import BaseModel
from typing import List, Optional

class TrackKeyStats(BaseModel):
    album_id: Optional[int] = None
    album_name: str
    key: str
    count: int  # Corregido de "count:" a "count" para estándar JSON