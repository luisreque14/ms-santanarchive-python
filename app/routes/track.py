from http.client import HTTPException

from fastapi import APIRouter
from fastapi.params import Query

from app.models.music import TrackResponse, GenreFilterResponse
from typing import List, Optional

from app.services.tracks_service import TracksService

router = APIRouter()

@router.get("/", response_model=List[TrackResponse])
async def get_tracks(album: Optional[int] = Query(None)):
    return await TracksService.get_tracks(album)

@router.get("/by-genre/{genre_id}", response_model=GenreFilterResponse)
async def get_tracks_by_genre(genre_id: int):
    data = await TracksService.get_tracks_by_genre_logic(genre_id)
    if not data:
        raise HTTPException(status_code=404, detail="Pistas no encontradas")
    return data

@router.get("/by-range", response_model=List[TrackResponse])
async def get_tracks_range(
    start: int = Query(..., description="Año de inicio", example=1970),
    end: int = Query(..., description="Año de fin", example=1980)
):
    data = await TracksService.get_tracks_by_date_range(start, end)
    if not data:
        raise HTTPException(status_code=404, detail="Pistas no encontradas")
    return data
