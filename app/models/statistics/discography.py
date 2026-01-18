from pydantic import BaseModel
from typing import List, Optional

class InstrumentalStatsResponse(BaseModel):
    album_id: Optional[int] = None
    album_name: str
    total_instrumental: int
    total_vocal: int

class TrackKeyStats(BaseModel):
    album_id: Optional[int] = None
    album_name: str
    key: str
    count: int

class ExecutiveSummaryResponse(BaseModel):
    total_tracks: int
    instrumental_percentage: float
    love_songs_percentage: float
    most_used_key: str

class LoveSongStatsResponse(BaseModel):
    total_tracks: int
    love_songs_count: int
    non_love_songs_count: int
    love_songs_percentage: float
    non_love_songs_percentage: float

class MusicalGenreStatsResponse(BaseModel):
    genre_id: int
    genre_name: str
    track_count: int
    percentage: float

class GuestArtistReportResponse(BaseModel):
    period: str
    total_tracks: int
    guest_artist_tracks: int
    guest_artist_percentage: float
    guestArtists: List[str]