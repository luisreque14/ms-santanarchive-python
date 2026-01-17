from fastapi import HTTPException
from app.repositories.track_repository import TrackRepository
from typing import Optional

class TrackService:
    def __init__(self, repository: TrackRepository):
        self.repo = repository

    async def list_tracks(self, album_id: Optional[int] = None):
        match_stage = {"album_id": album_id} if album_id else {}
        return await self.repo.get_tracks_with_details(match_stage)

    async def list_tracks_by_genre(self, genre_id: int):
        genre_info = await self.repo.get_genre_by_id(genre_id)
        if not genre_info:
            raise HTTPException(status_code=404, detail="Genre not found")
        
        match_stage = {"genre_ids": genre_id}
        tracks = await self.repo.get_tracks_with_details(match_stage)
        
        return {
            "genre_name": genre_info["name"],
            "tracks": tracks
        }

    async def list_collaborations_by_range(self, start: int, end: int):
        # Lógica: Validar que el rango sea coherente
        if start > end:
            raise HTTPException(status_code=400, detail="Start year cannot be greater than end year")
        return await self.repo.get_tracks_by_date_range_pipeline(start, end)