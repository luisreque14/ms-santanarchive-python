from fastapi import APIRouter, HTTPException, Query
from app.services.statistics_service import StatisticsService
from app.models.statistics.discography import (
    LoveSongStatsResponse,
    ExecutiveSummaryResponse,
    TrackKeyStats,
    InstrumentalStatsResponse, MusicalGenreStatsResponse
)
from typing import List, Optional

router = APIRouter()

@router.get("/instrumental-tracks", response_model=InstrumentalStatsResponse)
async def get_instrumental_stats(album_id: Optional[int] = Query(None)):
    data = await StatisticsService.get_instrumental_logic(album_id)
    if not data: raise HTTPException(404, "No hay datos")
    return data

@router.get("/tone-stats", response_model=List[TrackKeyStats])
async def get_key_stats(album_id: Optional[int] = Query(None)):
    return await StatisticsService.get_key_stats_logic(album_id)

@router.get("/executive-summary", response_model=ExecutiveSummaryResponse)
async def get_summary():
    # Asumiendo que moviste la lógica al servicio
    data = await StatisticsService.get_executive_summary_logic()
    if not data: raise HTTPException(404, "Error al generar resumen")
    return data

@router.get("/love-songs", response_model=LoveSongStatsResponse)
async def get_love_songs_stats():
    data = await StatisticsService.get_love_song_stats_logic()
    if not data:
        raise HTTPException(status_code=404, detail="No data found")
    return data

@router.get("/musical-genres", response_model=List[MusicalGenreStatsResponse])
async def get_genre_stats():
    results = await StatisticsService.get_genre_stats_logic()
    if not results:
        raise HTTPException(status_code=404, detail="No se encontraron géneros")
    return results