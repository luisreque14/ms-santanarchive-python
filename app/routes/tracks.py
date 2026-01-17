from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.repositories.track_repository import TrackRepository
from app.services.track_service import TrackService
from typing import Optional

router = APIRouter()

def get_track_service(db=Depends(get_db)):
    return TrackService(TrackRepository(db))

@router.get("/")
async def get_tracks(
    album_id: Optional[int] = Query(None), 
    service: TrackService = Depends(get_track_service)
):
    return await service.list_tracks(album_id)

@router.get("/genre/{genre_id}")
async def get_by_genre(
    genre_id: int, 
    service: TrackService = Depends(get_track_service)
):
    return await service.list_tracks_by_genre(genre_id)

@router.get("/collaborations/range")
async def get_collab_range(
    start: int, 
    end: int, 
    service: TrackService = Depends(get_track_service)
):
    return await service.list_collaborations_by_range(start, end)