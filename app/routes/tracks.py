from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.repositories.track_repository import TrackRepository
from app.services.track_service import TrackService
from app.dtos.track_dto import TrackDto, GenreFilterDto
from typing import List, Optional

router = APIRouter(prefix="/tracks", tags=["Tracks"])

def get_track_service(db=Depends(get_db)):
    return TrackService(TrackRepository(db))

@router.get(
    "/", 
    response_model=List[TrackDto],
    response_model_by_alias=True
)
async def get_tracks(
    album_id: Optional[int] = Query(None), 
    service: TrackService = Depends(get_track_service)
):
    """
    Obtiene la lista de canciones, opcionalmente filtradas por álbum.
    Incluye metadatos (tonalidad, instrumental, etc.) en camelCase.
    """
    return await service.list_tracks(album_id)

@router.get(
    "/album/{album_id}", 
    response_model=List[TrackDto],
    response_model_by_alias=True
)
async def get_tracks_by_album(
    album_id: int, 
    service: TrackService = Depends(get_track_service)
):
    """
    Obtiene la lista de canciones, opcionalmente filtradas por álbum.
    Incluye metadatos (tonalidad, instrumental, etc.) en camelCase.
    """
    return await service.list_tracks(album_id)

@router.get(
    "/genre/{genre_id}", 
    response_model=GenreFilterDto,
    response_model_by_alias=True
)
async def get_by_genre(
    genre_id: int, 
    service: TrackService = Depends(get_track_service)
):
    """
    Obtiene todas las canciones de un género específico.
    """
    return await service.list_tracks_by_genre(genre_id)

@router.get(
    "/collaborations/range", 
    response_model=List[TrackDto],
    response_model_by_alias=True
)
async def get_collab_range(
    start: int, 
    end: int, 
    service: TrackService = Depends(get_track_service)
):
    """
    Filtra colaboraciones por un rango de años (ej. 1970 a 1980).
    """
    return await service.list_collaborations_by_range(start, end)