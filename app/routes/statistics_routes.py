from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from app.services.statistics_service import StatisticsService
from app.dtos.statistics.executive_summary_dto import ExecutiveSummaryDto
from app.dtos.statistics.discography.track_key_dto import TrackKeyStatsDto
from app.dtos.statistics.discography_dto import (
    InstrumentalStatsDto,
    LoveSongStatsDto,
    MusicalGenreStatsDto,
    GuestArtistReportDto
    )
from app.core.dependencies import get_stats_service

router = APIRouter(prefix="/statistics", tags=["Statistics"])

@router.get(
    "/instrumental-tracks", 
    response_model=InstrumentalStatsDto,
    response_model_by_alias=True
)
async def get_instrumental_stats(
    album_id: Optional[int] = Query(None),
    service: StatisticsService = Depends(get_stats_service)
    ):
    data = await service.get_instrumental_logic(album_id)
    if not data:
        raise HTTPException(status_code=404, detail="No data found for instrumental stats")
    return data

@router.get(
    "/tone-stats", 
    # Mapea 'count' a 'totalTracks' y 'key' a 'musicalKey'
    response_model=List[TrackKeyStatsDto],
    response_model_by_alias=True
)
async def get_key_stats(
    album_id: Optional[int] = Query(None),
    service: StatisticsService = Depends(get_stats_service)
):
    return await service.get_key_stats_logic(album_id)

@router.get(
    "/executive-summary", 
    response_model=ExecutiveSummaryDto,
    response_model_by_alias=True
)
async def get_executive_summary(
    service: StatisticsService = Depends(get_stats_service)
):
    data = await service.get_executive_summary_logic()
    if not data:
        raise HTTPException(status_code=404, detail="Could not generate executive summary")
    return data

@router.get(
    "/love-songs", 
    response_model=LoveSongStatsDto,
    response_model_by_alias=True
)
async def get_love_song_stats(
    service: StatisticsService = Depends(get_stats_service)
):
    data = await service.get_love_song_stats_logic()
    if not data:
        raise HTTPException(status_code=404, detail="No love song data available")
    return data

@router.get(
    "/musical-genres", 
    response_model=List[MusicalGenreStatsDto],
    response_model_by_alias=True
)
async def get_musical_genre_stats(
    service: StatisticsService = Depends(get_stats_service)
):
    return await service.get_musical_genre_stats_logic()

@router.get(
    "/guest-artists", 
    response_model=List[GuestArtistReportDto],
    response_model_by_alias=True
)
async def get_guest_artists_report(
    service: StatisticsService = Depends(get_stats_service)
):
    return await service.get_guest_artists_report_logic()