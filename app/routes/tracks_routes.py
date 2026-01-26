from fastapi import APIRouter, Depends, Query
from app.services.track_service import TrackService
from app.dtos.track_dto import TrackDto, GenreFilterDto, TrackWithAlbumDetailsDto
from typing import List, Optional
from app.core.dependencies import get_track_service

router = APIRouter(prefix="/tracks", tags=["Tracks"])

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
async def get_by_album(
    album_id: int, 
    service: TrackService = Depends(get_track_service)
):
    """
    Obtiene la lista de canciones, opcionalmente filtradas por álbum.
    Incluye metadatos (tonalidad, instrumental, etc.) en camelCase.
    """
    return await service.get_by_album(album_id)

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
    return await service.get_by_genre(genre_id)

@router.get(
    "/by-guest-artists-range", 
    response_model=List[TrackWithAlbumDetailsDto],
    response_model_by_alias=True
)
async def get_by_guest_artists_range(
    start: int, 
    end: int, 
    service: TrackService = Depends(get_track_service)
):
    """
    Filtra colaboraciones por un rango de años (ej. 1970 a 1980).
    """
    return await service.get_by_guest_artists_range(start, end)

@router.get(
    "/by-top-duration", 
    response_model=List[TrackWithAlbumDetailsDto],
    response_model_by_alias=True
)
async def get_by_top_duration(
    sort: str = Query(""), 
    isLive: bool | None = Query(None), 
    service: TrackService = Depends(get_track_service)
):
    return await service.get_by_top_duration(isLive, sort)

@router.get(
    "/by-lead-vocal", 
    response_model=List[TrackWithAlbumDetailsDto],
    response_model_by_alias=True
)
async def get_by_lead_vocal(
    musicianId: int = Query(0), 
    service: TrackService = Depends(get_track_service)
):
    return await service.get_by_lead_vocal(musicianId)

@router.get(
    "/by-live-in-studio-albums", 
    response_model=List[TrackWithAlbumDetailsDto],
    response_model_by_alias=True
)
async def get_by_live_in_studio_albums(
    service: TrackService = Depends(get_track_service)
):
    return await service.get_by_live_in_studio_albums()

@router.get(
    "/by-composer", 
    response_model=List[TrackWithAlbumDetailsDto],
    response_model_by_alias=True
)
async def get_by_composer_id(
    composerId: int = Query(0), 
    service: TrackService = Depends(get_track_service)
):
    return await service.get_by_composer_id(composerId)