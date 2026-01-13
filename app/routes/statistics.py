from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from app.services.statistics_service import StatisticsService
from app.models.statistics.discography import (
    InstrumentalStatsResponse, TrackKeyStats, ExecutiveSummaryResponse
)

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