from pydantic import BaseModel

class ExecutiveSummaryResponse(BaseModel):
    total_tracks: int
    instrumental_percentage: float
    love_songs_percentage: float
    most_used_key: str