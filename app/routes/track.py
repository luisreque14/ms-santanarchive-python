from http.client import HTTPException

from fastapi import APIRouter
from fastapi.params import Query

from app.models.music import TrackResponse, GenreFilterResponse
from typing import List, Optional

from app.services.tracks_service import TracksService

router = APIRouter()

@router.get("/", response_model=List[TrackResponse])
async def get_tracks(album: Optional[int] = Query(None)): # Cambiado a int
    return await TracksService.get_tracks(album)

@router.get("/by-genre/{genre_id}", response_model=GenreFilterResponse)
async def get_tracks_by_genre(genre_id: int):
    data = await TracksService.get_tracks_by_genre_logic(genre_id)
    if not data:
        raise HTTPException(status_code=404, detail="Género no encontrado")
    return data